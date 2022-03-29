from collections import defaultdict
from functools import reduce

from dying.models import DyingIssue, DyingUnit
from essentials.choices import PersonChoices
from essentials.models import Person
from ledgers.models import Ledger
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from transactions.choices import TransactionChoices

from .models import Formula, RawLotDetail, RawProduct, RawTransaction, RawTransactionLot
from .utils import calculate_amount, is_array_unique


class FormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formula
        fields = [
            "id",
            "denominator",
            "numerator",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        return super().create(validated_data)


class RawProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawProduct
        fields = [
            "id",
            "name",
            "person",
            "type",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        if data["person"].person_type == PersonChoices.CUSTOMER:
            raise serializers.ValidationError(
                "Customer can not have a raw product",
                status.HTTP_400_BAD_REQUEST,
            )
        branch = self.context["request"].branch
        if RawProduct.objects.filter(
            name=data["name"],
            person=data["person"],
            type=data["type"],
            branch=branch,
        ).exists():
            raise serializers.ValidationError(
                "This product already exists",
                status.HTTP_400_BAD_REQUEST,
            )
        return data

    def create(self, validated_data):

        validated_data["branch"] = self.context["request"].branch
        return super().create(validated_data)


class RawLotDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawLotDetail
        fields = [
            "id",
            "lot_number",
            "quantity",
            "actual_gazaana",
            "expected_gazaana",
            "formula",
            "warehouse",
            "nature",
            "rate",
        ]
        read_only_fields = ["id", "lot_number"]


class RawTransactionLotSerializer(serializers.ModelSerializer):

    lot_detail = RawLotDetailsSerializer(many=True)
    dying_unit = serializers.UUIDField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = RawTransactionLot
        fields = [
            "id",
            "raw_transaction",
            "lot_number",
            "issued",
            "lot_detail",
            "dying_unit",
            "raw_product",
        ]
        read_only_fields = [
            "id",
            "lot_number",
            "raw_transaction",
        ]


def create_ledger_entry(raw_transaction, ledger_string, amount, branch):
    Ledger.objects.create(
        detail=ledger_string,
        nature="C",
        raw_transaction=raw_transaction,
        person=raw_transaction.person,
        date=raw_transaction.date,
        amount=amount,
        branch=branch,
    )


class CreateRawTransactionSerializer(serializers.ModelSerializer):

    lots = RawTransactionLotSerializer(many=True)

    class Meta:
        model = RawTransaction
        fields = [
            "id",
            "person",
            "manual_invoice_serial",
            "date",
            "lots",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        branch = self.context["request"].branch
        if RawTransaction.objects.filter(
            branch=branch, manual_invoice_serial=data["manual_invoice_serial"]
        ).exists():
            raise serializers.ValidationError(
                "This book number exists", status.HTTP_400_BAD_REQUEST
            )

        return data

    def create(self, validated_data):
        lots = validated_data.pop("lots")
        branch = self.context["request"].branch
        transaction = RawTransaction.objects.create(
            **validated_data,
            branch=branch,
        )

        ledger_string = "Kora wasooli\n"
        amount = 0
        for lot in lots:
            current_lot = RawTransactionLot.objects.create(
                raw_transaction=transaction,
                issued=lot["issued"],
                raw_product=lot["raw_product"],
                branch=branch,
                lot_number=RawTransactionLot.get_next_serial(branch),
            )
            ledger_string += f"Lot # {current_lot.lot_number}\n"
            if current_lot.issued:
                dying = DyingUnit.objects.get(id=lot["dying_unit"])
                try:
                    DyingIssue.objects.create(
                        dying_unit=dying,
                        lot_number=current_lot,
                        dying_lot_number=DyingIssue.next_serial(branch),
                        date=transaction.date,
                        branch=branch,
                    )
                except ValidationError:
                    raise serializers.ValidationError(
                        "Please enter dying unit for issued lot"
                    )

            # ensure that warehouse is added if lot is not for issue
            # also ensure that the product belongs to the person
            for lot_detail in lot["lot_detail"]:
                if not current_lot.issued and not lot_detail["warehouse"]:
                    raise serializers.ValidationError(
                        "Add warehouse for the non-issue lot",
                        status.HTTP_400_BAD_REQUEST,
                    )
                if transaction.person != transaction.person:
                    raise serializers.ValidationError(
                        "The product does not belong to the supplier",
                        status.HTTP_400_BAD_REQUEST,
                    )

            current_lot_detail = map(
                lambda l: {
                    **l,
                    "warehouse": None if current_lot.issued else l["warehouse"],
                },
                lot["lot_detail"],
            )

            for detail in current_lot_detail:
                current_detail = RawLotDetail.objects.create(
                    **detail, lot_number=current_lot, branch=branch
                )
                amount += (
                    current_detail.quantity
                    * current_detail.rate
                    * current_detail.actual_gazaana
                    * (
                        current_detail.formula.numerator
                        / current_detail.formula.denominator
                    )
                )

        create_ledger_entry(transaction, ledger_string, amount, branch)

        return {
            "id": transaction.id,
            "person": transaction.person,
            "manual_invoice_serial": transaction.manual_invoice_serial,
            "date": transaction.date,
            "lots": lots,
        }


class RawStockAwareSerializer(serializers.Serializer):
    class Serializer(serializers.Serializer):

        lot_number = serializers.UUIDField(write_only=True)
        detail = RawLotDetailsSerializer(many=True, write_only=True)

    data = Serializer(many=True, write_only=True)
    branch = None
    amount = 0

    # make sure lot numbers are unique
    def validate(self, data):
        if not is_array_unique(data["data"], "lot_number"):
            raise ValidationError(
                "Lot numbers must be unique", status.HTTP_400_BAD_REQUEST
            )
        return data

    def check_stock(self, array, check_person=False, person=None):
        self.branch = self.context["request"].branch
        stock = RawLotDetail.get_lot_stock(self.branch)
        for data in array:
            try:
                lot = RawTransactionLot.objects.get(
                    id=data["lot_number"], branch=self.branch
                )
            except Exception:
                raise ValidationError(f"Lot does not exist", status.HTTP_400_BAD_REQUEST)

            if check_person and lot.raw_transaction.person != person:
                raise ValidationError(
                    f"Lot {lot.lot_number} does not belong to this person"
                )

            for detail in data["detail"]:
                lot_stock = list(
                    filter(
                        lambda val: val["lot_number"] == lot.id
                        and val["actual_gazaana"] == detail["actual_gazaana"]
                        and val["expected_gazaana"] == detail["expected_gazaana"]
                        and val["formula"] == detail["formula"].id
                        and val["warehouse"] == detail["warehouse"].id,
                        stock,
                    )
                )
                quantity = reduce(
                    lambda prev, curr: prev
                    + (
                        curr["quantity"]
                        if curr["nature"] == TransactionChoices.CREDIT
                        else -curr["quantity"]
                    ),
                    lot_stock,
                    0,
                )
                if quantity < detail["quantity"]:
                    raise ValidationError(
                        f"Stock for lot # {lot.lot_number} is low",
                        status.HTTP_400_BAD_REQUEST,
                    )

    def create_detail_entries(self, validated_data):

        for data in validated_data["data"]:
            current_details = []
            lot = RawTransactionLot.objects.get(id=data["lot_number"])
            for detail in data["detail"]:
                current_details.append(
                    RawLotDetail(
                        lot_number=lot,
                        **detail,
                        nature=TransactionChoices.DEBIT,
                        branch=self.branch,
                    )
                )
            RawLotDetail.objects.bulk_create(current_details)

    def set_amount(self, validated_data):
        _amount = 0
        for data in validated_data["data"]:
            _amount += calculate_amount(data["detail"])
        self.amount = _amount

    class Meta:
        abstract = True


class RawReturnSerializer(RawStockAwareSerializer):

    person = serializers.UUIDField(write_only=True)

    def create(self, validated_data):
        person = Person.objects.get(id=validated_data["person"])
        self.check_stock(validated_data["data"], True, person)
        self.create_detail_entries(validated_data)
        self.set_amount(validated_data)
        Ledger.objects.create(
            detail="Kora maal wapsi",
            nature="D",
            person=person,
            amount=self.amount,
            branch=self.branch,
        )
        return {}


class RawLotNumberAndIdSerializer(serializers.ModelSerializer):

    class Meta:
        model = RawTransactionLot
        fields = ['id', 'lot_number']
