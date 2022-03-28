from dying.models import DyingIssue
from essentials.choices import PersonChoices
from ledgers.models import Ledger
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from .models import Formula, RawLotDetail, RawProduct, RawTransaction, RawTransactionLot


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
        fields = ["id", "name", "person", "type"]
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
                "This product already exists", status.HTTP_400_BAD_REQUEST
            )
        return data

    def create(self, validated_data):

        validated_data["branch"] = self.context["request"].branch
        return super().create(validated_data)


class RawLotDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "lot_number",
            "quantity",
            "actual_gazaana",
            "expected_gazaana",
            "formula",
            "warehouse",
            "nature",
        ]
        read_only_fields = ["id"]


class RawTransactionLotSerializer(serializers.ModelSerializer):

    lot_details = RawLotDetailsSerializer(many=True)
    dying_unit = serializers.UUIDField(required=False, write_only=True)

    class Meta:
        fields = [
            "id",
            "raw_transaction",
            "lot_number",
            "issued",
            "lot_details",
            "dying_unit",
        ]
        read_only_fields = ["id", "lot_number"]


def create_ledger_entry(raw_transaction, ledger_string, amount):
    Ledger.objects.create(
        detail=ledger_string,
        nature="C",
        raw_transaction=raw_transaction,
        person=raw_transaction.person,
        date=raw_transaction.date,
        amount=amount,
    )


class CreateRawTransactionSerializer(serializers.ModelSerializer):

    lots = RawTransactionLotSerializer(many=True)

    class Meta:
        model = RawTransaction
        fields = ["id", "person", "manual_invoice_serial", "date", "lots"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        lots = validated_data.pop("lots")
        branch = self.context["request"].branch
        transaction = RawTransaction.objects.create(**validated_data, branch=branch)

        ledger_string = "Kora wasooli\n"
        amount = 0
        for lot in lots:
            current_lot = RawTransactionLot.objects.create(
                raw_transaction=transaction,
                issues=lot["issued"],
                raw_product=lot["raw_product"],
                branch=branch,
                lot_number=RawTransactionLot.get_next_serial(branch),
            )
            ledger_string += f"Lot # {current_lot.lot_number}\n"
            if current_lot.issue:
                try:
                    DyingIssue.objects.create(
                        dying_unit=lot["dying_unit"],
                        lot_number=current_lot,
                        dying_lot_number=DyingIssue.next_serial(),
                        date=transaction.date,
                    )
                except ValidationError:
                    raise serializers.ValidationError(
                        "Please enter dying unit for issued lot"
                    )

            # ensure that warehouse is added if lot is not for issue
            # also ensure that the product belongs to the person
            for lot in lot["lot_detail"]:
                if not lot["issue"] and not lot["warehouse"]:
                    raise serializers.ValidationError(
                        "Add warehouse for the non-issue lot",
                        status.HTTP_400_BAD_REQUEST,
                    )
                if transaction.person != lot["person"]:
                    raise serializers.ValidationError(
                        "The product does not belong to the supplier",
                        status.HTTP_400_BAD_REQUEST,
                    )

            current_lot_detail = map(
                lambda l: {
                    **l,
                    "warehouse": None if current_lot.issue else l["warehouse"],
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

        create_ledger_entry(transaction, ledger_string, amount)

        return {**transaction, "lots": lots}
