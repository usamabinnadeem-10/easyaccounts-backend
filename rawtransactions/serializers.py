from functools import reduce

from dying.models import DyingIssue
from essentials.choices import PersonChoices
from essentials.models import Warehouse
from ledgers.models import Ledger, LedgerAndRawTransaction
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from transactions.choices import TransactionChoices

from .choices import RawDebitTypes
from .models import (
    Formula,
    RawDebit,
    RawDebitLot,
    RawDebitLotDetail,
    RawLotDetail,
    RawProduct,
    RawTransaction,
    RawTransactionLot,
)
from .utils import calculate_amount, get_all_raw_stock, is_array_unique


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
            person__branch=branch,
        ).exists():
            raise serializers.ValidationError(
                "This product already exists",
                status.HTTP_400_BAD_REQUEST,
            )
        return data

    def create(self, validated_data):
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
            "rate",
        ]
        read_only_fields = ["id", "lot_number"]


class RawTransactionLotSerializer(serializers.ModelSerializer):

    lot_detail = RawLotDetailsSerializer(many=True)
    dying_unit = serializers.UUIDField(required=False, allow_null=True)

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


class CreateRawTransactionSerializer(serializers.ModelSerializer):

    lots = RawTransactionLotSerializer(many=True, required=True)

    class Meta:
        model = RawTransaction
        fields = ["id", "person", "date", "lots"]
        read_only_fields = [
            "id",
        ]

    # def validate(self, data):
    #     branch = self.context["request"].branch
    #     # if RawTransaction.objects.filter(
    #     #     person__branch=branch, manual_invoice_serial=data["manual_invoice_serial"]
    #     # ).exists():
    #     #     raise serializers.ValidationError(
    #     #         "This book number exists", status.HTTP_400_BAD_REQUEST
    #     #     )
    #     # next_serial = RawTransaction.get_next_serial(
    #     #     "manual_invoice_serial", person__branch=branch
    #     # )
    #     # if data["manual_invoice_serial"] != next_serial:
    #     #     raise serializers.ValidationError(
    #     #         f"Please use book number {next_serial}", status.HTTP_400_BAD_REQUEST
    #     #     )

    #     return data

    def create(self, validated_data):
        lots = validated_data.pop("lots")
        branch = self.context["request"].branch
        user = self.context["request"].user
        transaction = RawTransaction.objects.create(
            **validated_data,
            serial=RawTransaction.get_next_serial("serial", person__branch=branch),
            user=user,
        )

        amount = 0
        for lot in lots:
            current_lot = RawTransactionLot.objects.create(
                raw_transaction=transaction,
                issued=lot["issued"],
                raw_product=lot["raw_product"],
                lot_number=RawTransactionLot.get_next_serial(
                    "lot_number", raw_transaction__person__branch=branch
                ),
            )
            if current_lot.issued:
                try:
                    DyingIssue.create_auto_issued_lot(
                        branch=branch,
                        dying_unit=lot["dying_unit"],
                        lot_number=current_lot,
                        date=transaction.date,
                    )
                except:
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
                    **detail, lot_number=current_lot
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
        if transaction.person:
            LedgerAndRawTransaction.create_ledger_entry(transaction, amount)

        return {
            "id": transaction.id,
            "person": transaction.person,
            # "manual_invoice_serial": transaction.manual_invoice_serial,
            "date": transaction.date,
            "lots": lots,
        }


class UniqueLotNumbers:
    """This class ensures that all lot numbers in the array are unique"""

    # make sure lot numbers are unique
    def validate(self, data):
        if not is_array_unique(data["data"], "lot_number"):
            raise ValidationError(
                "Lot numbers must be unique", status.HTTP_400_BAD_REQUEST
            )
        return data


class StockCheck:
    """This class checks if the stock is low for any lot"""

    branch = None

    def check_stock(self, array, check_person=False, person=None):
        self.branch = self.context["request"].branch
        stock = get_all_raw_stock(self.branch)
        for data in array:
            lot = data["lot_number"]
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


class RawDebitSerializer(UniqueLotNumbers, StockCheck, serializers.ModelSerializer):
    class Serializer(serializers.ModelSerializer):

        detail = RawLotDetailsSerializer(many=True, required=True)

        class Meta:
            model = RawDebitLot
            fields = ["lot_number", "detail"]

    data = Serializer(many=True)

    class Meta:
        model = RawDebit
        fields = [
            "id",
            "person",
            # "manual_invoice_serial",
            "bill_number",
            "date",
            "data",
            "debit_type",
        ]
        read_only_fields = ["id", "bill_number"]

    def validate(self, data):
        super().validate(data)
        # if not RawDebit.is_serial_unique(
        #     manual_invoice_serial=data["manual_invoice_serial"],
        #     debit_type=data["debit_type"],
        #     branch=self.context["request"].branch,
        # ):
        #     raise ValidationError(f"Serial # {data['manual_invoice_serial']} exists")
        if not data["person"]:
            raise ValidationError("Please choose a person", status.HTTP_400_BAD_REQUEST)

        return data

    def create(self, validated_data):
        data = validated_data.pop("data")
        user = self.context["request"].user
        check_person = (
            True if validated_data["debit_type"] == RawDebitTypes.RETURN else False
        )
        person = validated_data["person"] if check_person else None
        self.check_stock(data, check_person, person)
        debit_instance = RawDebit.objects.create(
            **validated_data,
            user=user,
            bill_number=RawDebit.get_next_serial(
                "serial",
                debit_type=validated_data["debit_type"],
                person__branch=self.branch,
            ),
        )

        ledger_amount = 0
        for lot in data:
            ledger_amount += calculate_amount(lot["detail"])
            raw_debit_lot_instance = RawDebitLot.objects.create(
                lot_number=lot["lot_number"],
                bill_number=debit_instance,
            )
            current_return_details = []
            for detail in lot["detail"]:
                current_return_details.append(
                    RawDebitLotDetail(
                        return_lot=raw_debit_lot_instance,
                        branch=self.branch,
                        **detail,
                    )
                )

            RawDebitLotDetail.objects.bulk_create(current_return_details)

        Ledger.objects.create(
            # raw_debit=debit_instance,
            nature="D",
            # detail="Kora maal wapsi"
            # if debit_instance.debit_type == RawDebitTypes.RETURN
            # else "Kora sale",
            person=debit_instance.person,
            amount=ledger_amount,
            branch=self.branch,
        )

        validated_data["data"] = data
        return validated_data


class RawLotNumberAndIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawTransactionLot
        fields = ["id", "lot_number"]


class ListRawTransactionSerializer(serializers.ModelSerializer):
    class LotSerializer(serializers.ModelSerializer):

        raw_lot_detail = RawLotDetailsSerializer(many=True)

        class Meta:
            model = RawTransactionLot
            fields = [
                "id",
                "raw_transaction",
                "lot_number",
                "issued",
                "raw_product",
                "raw_lot_detail",
            ]

    transaction_lot = LotSerializer(many=True)

    class Meta:
        model = RawTransaction
        fields = fields = [
            "id",
            "person",
            "manual_invoice_serial",
            "date",
            "transaction_lot",
        ]


class ViewAllStockSerializer(serializers.Serializer):

    quantity = serializers.FloatField()
    actual_gazaana = serializers.FloatField()
    expected_gazaana = serializers.FloatField()
    raw_product = serializers.UUIDField()
    warehouse = serializers.UUIDField()
    formula = serializers.UUIDField()
    # nature = serializers.CharField()


class RawLotDetailWithTransferWarehouse(serializers.ModelSerializer):

    to_warehouse = serializers.UUIDField(required=True)

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
            "to_warehouse",
        ]
        read_only_fields = ["id", "lot_number"]


class RawStockTransferSerializer(
    UniqueLotNumbers, StockCheck, serializers.ModelSerializer
):
    class Serializer(serializers.ModelSerializer):

        detail = RawLotDetailWithTransferWarehouse(many=True, required=True)

        class Meta:
            model = RawDebitLot
            fields = ["lot_number", "detail"]

    data = Serializer(many=True, required=True)

    class Meta:
        model = RawDebit
        fields = [
            "id",
            # "manual_invoice_serial",
            "bill_number",
            "date",
            "data",
            "debit_type",
        ]
        read_only_fields = ["id", "bill_number"]

    def validate(self, data):
        super().validate(data)
        # if not RawDebit.is_serial_unique(
        #     manual_invoice_serial=data["manual_invoice_serial"],
        #     debit_type=data["debit_type"],
        #     branch=self.context["request"].branch,
        # ):
        #     raise ValidationError(f"Serial # {data['manual_invoice_serial']} exists")

        if data["debit_type"] != RawDebitTypes.TRANSFER:
            raise ValidationError(
                "Please choose transfer type", status.HTTP_400_BAD_REQUEST
            )

        return data

    def create(self, validated_data):
        data = validated_data.pop("data")
        self.check_stock(data)
        debit_instance = RawDebit.objects.create(
            **validated_data,
            branch=self.branch,
            bill_number=RawDebit.get_next_serial(
                "serial",
                debit_type=validated_data["debit_type"],
                person__branch=self.branch,
            ),
        )

        for lot in data:
            raw_debit_lot_instance = RawDebitLot.objects.create(
                lot_number=lot["lot_number"],
                bill_number=debit_instance,
            )
            current_return_details = []
            for detail in lot["detail"]:
                try:
                    to_warehouse = Warehouse.objects.get(
                        id=detail["to_warehouse"], branch=self.branch
                    )
                except:
                    raise ValidationError(
                        "This warehouse does not exist", status.HTTP_400_BAD_REQUEST
                    )

                if to_warehouse.id == detail["warehouse"].id:
                    raise ValidationError(
                        f"Both warehouse are same in lot# {lot['lot_number'].lot_number}",
                        status.HTTP_400_BAD_REQUEST,
                    )

                obj = {**detail, "nature": TransactionChoices.DEBIT, "rate": 1.0}
                del obj["to_warehouse"]
                current_return_details.append(
                    RawDebitLotDetail(
                        return_lot=raw_debit_lot_instance,
                        **obj,
                    )
                )
                obj["nature"] = TransactionChoices.CREDIT
                obj["warehouse"] = to_warehouse
                current_return_details.append(
                    RawDebitLotDetail(
                        return_lot=raw_debit_lot_instance,
                        **obj,
                    )
                )

            RawDebitLotDetail.objects.bulk_create(current_return_details)
        validated_data["data"] = data
        return validated_data
