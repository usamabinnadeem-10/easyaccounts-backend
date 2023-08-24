import copy
from functools import reduce

from django.forms import model_to_dict
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from essentials.choices import PersonChoices
from ledgers.models import LedgerAndRawDebit, LedgerAndRawTransaction

from .models import (
    Formula,
    RawDebit,
    RawDebitLot,
    RawLotDetail,
    RawProduct,
    RawTransaction,
    RawTransactionLot,
    RawTransfer,
    RawTransferLot,
    RawTransferLotDetail,
)
from .utils import is_array_unique, validate_raw_inventory


class RawTransactionValidationHelper:
    def validate_warehouse_and_lot_issued(self, transaction_data):
        """validates if warehouses are added if lot is not issued for raw transaction"""
        lots = transaction_data["lots"]
        for index, lot in enumerate(lots):
            issued = lot["issued"]
            for lot_detail in lot["lot_detail"]:
                has_warehouse = lot_detail.get("warehouse", None)
                if has_warehouse and issued:
                    raise serializers.ValidationError(
                        f"Warehouse can not be added for issued lot # {index + 1}",
                        status.HTTP_400_BAD_REQUEST,
                    )
                if not issued and not has_warehouse:
                    raise serializers.ValidationError(
                        f"Add warehouse for non-issued lot # {index + 1}",
                        status.HTTP_400_BAD_REQUEST,
                    )


class RawLotNumberAndIdSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = RawTransactionLot
        fields = ["id", "lot_number", "raw_product"]


class UniqueLotNumbers:
    """This class ensures that all lot numbers in the array are unique"""

    # make sure lot numbers are unique
    def validate(self, data):
        if not is_array_unique(data["data"], "lot_number"):
            raise ValidationError(
                "Lot numbers must be unique", status.HTTP_400_BAD_REQUEST
            )
        return data


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
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        branch = self.context["request"].branch
        if RawProduct.objects.filter(
            name=data["name"],
            branch=branch,
        ).exists():
            raise serializers.ValidationError(
                "This product already exists",
                status.HTTP_400_BAD_REQUEST,
            )
        return data

    def create(self, validated_data):
        branch = self.context["request"].branch
        product = RawProduct.objects.create(
            name=validated_data.get("name"), branch=branch
        )
        return product


"""Lot Detail Serializer - Common"""


class RawLotDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawLotDetail
        fields = [
            "id",
            "lot_number",
            "quantity",
            "actual_gazaana",
            "expected_gazaana",
            "rate_gazaana",
            "formula",
            "warehouse",
            "rate",
        ]
        read_only_fields = ["id", "lot_number"]


"""Raw Transaction Serializers"""


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
            "product_glue",
            "product_type",
            "detail",
            "dying_number",
            "warehouse_number",
        ]
        read_only_fields = ["id", "lot_number", "raw_transaction"]
        extra_kwargs = {
            "dying_number": {"allow_null": True, "required": False},
            "warehouse_number": {"allow_null": True, "required": False},
        }


class CreateRawTransactionSerializer(
    RawTransactionValidationHelper, serializers.ModelSerializer
):
    lots = RawTransactionLotSerializer(many=True, required=True, write_only=True)

    class Meta:
        model = RawTransaction
        fields = ["id", "person", "date", "manual_serial", "lots"]
        read_only_fields = [
            "id",
        ]

    def validate(self, data):
        self.validate_warehouse_and_lot_issued(data)
        return data

    def create(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        raw_transaction = RawTransaction.make_raw_transaction(
            copy.deepcopy(validated_data), branch, user
        )
        LedgerAndRawTransaction.create_ledger_entry(
            raw_transaction,
            RawTransaction.get_raw_transaction_total(validated_data),
            user,
        )

        return raw_transaction


class UpdateRawTransactionSerializer(
    RawTransactionValidationHelper, serializers.ModelSerializer
):
    class UpdateRawTransactionLotSerializer(serializers.ModelSerializer):
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
                "product_glue",
                "product_type",
                "detail",
                "dying_number",
                "warehouse_number",
            ]
            read_only_fields = ["id", "raw_transaction"]
            extra_kwargs = {"lot_number": {"required": False, "allow_null": True}}

    lots = UpdateRawTransactionLotSerializer(many=True, required=True)

    class Meta:
        model = RawTransaction
        fields = ["id", "person", "date", "manual_serial", "lots"]
        read_only_fields = [
            "id",
        ]

    def validate(self, data):
        self.validate_warehouse_and_lot_issued(data)
        return data

    def update(self, instance, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        raw_transaction = RawTransaction.make_raw_transaction(
            copy.deepcopy(validated_data), branch, user, old_instance=instance
        )
        validated, error = validate_raw_inventory(branch)
        if not validated:
            raise ValidationError(error)
        LedgerAndRawTransaction.create_ledger_entry(
            raw_transaction,
            RawTransaction.get_raw_transaction_total(validated_data),
            user,
        )
        return raw_transaction


class ListRawTransactionSerializer(serializers.ModelSerializer):
    class LotSerializer(serializers.ModelSerializer):
        lot_detail = RawLotDetailsSerializer(many=True)

        class Meta:
            model = RawTransactionLot
            fields = [
                "id",
                "raw_transaction",
                "lot_number",
                "issued",
                "raw_product",
                "product_glue",
                "product_type",
                "lot_detail",
                "detail",
                "warehouse_number",
                "dying_number",
            ]

    lots = LotSerializer(many=True)

    class Meta:
        model = RawTransaction
        fields = [
            "id",
            "person",
            "date",
            "serial",
            "date",
            "lots",
            "manual_serial",
        ]


# class StockCheck:
#     """This class checks if the stock is low for any lot"""

#     branch = None

#     def check_stock(self, array, check_person=False, person=None):
#         self.branch = self.context["request"].branch
#         stock = get_all_raw_stock(self.branch)
#         for data in array:
#             lot_number = data["lot_number"]
#             # if check_person and lot.raw_transaction.person != person:
#             #     raise ValidationError(
#             #         f"Lot {lot.lot_number} does not belong to this person"
#             #     )

#             for detail in data["detail"]:
#                 lot_stock = list(
#                     filter(
#                         lambda val: val["lot_number"] == lot_number
#                         and val["actual_gazaana"] == detail["actual_gazaana"]
#                         and val["expected_gazaana"] == detail["expected_gazaana"]
#                         # and val["formula"] == detail["formula"].id
#                         and val["warehouse"] == detail["warehouse"].id,
#                         stock,
#                     )
#                 )
#                 quantity = reduce(
#                     lambda prev, curr: prev
#                     + (
#                         curr["quantity"]
#                         if curr["nature"] == TransactionChoices.CREDIT
#                         else -curr["quantity"]
#                     ),
#                     lot_stock,
#                     0,
#                 )
#                 if quantity < detail["quantity"]:
#                     raise ValidationError(
#                         f"Stock for lot # {lot_number} is low",
#                         status.HTTP_400_BAD_REQUEST,
#                     )


"""Raw Debit Serializers"""


class RawDebitSerializer(UniqueLotNumbers, serializers.ModelSerializer):
    class Serializer(serializers.ModelSerializer):
        detail = RawLotDetailsSerializer(many=True, required=True)

        class Meta:
            model = RawDebitLot
            fields = ["lot_number", "detail"]

    data = Serializer(many=True, write_only=True)

    class Meta:
        model = RawDebit
        fields = ["id", "person", "date", "data", "debit_type", "manual_serial"]
        read_only_fields = ["id"]

    def validate(self, data):
        super().validate(data)
        if not data["person"]:
            raise ValidationError("Please choose a person", status.HTTP_400_BAD_REQUEST)
        return data

    def create_ledger_entry(self, validated_data, debit_instance):
        ledger_amount = reduce(
            lambda prev, curr: prev
            + reduce(
                lambda prev2, curr2: prev2
                + curr2["quantity"] * curr2["rate"] * curr2["rate_gazaana"],
                curr["detail"],
                0,
            ),
            validated_data["data"],
            0,
        )

        LedgerAndRawDebit.create_ledger_entry(
            debit_instance,
            nature="D",
            person=debit_instance.person,
            amount=ledger_amount,
        )

    def create_debit_entry(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        debit_instance = RawDebit.make_raw_debit_transaction(
            copy.deepcopy(validated_data), branch, user
        )
        validated, error = validate_raw_inventory(branch)
        if not validated:
            raise ValidationError(error)
        return debit_instance

    def create(self, validated_data):
        debit_instance = self.create_debit_entry(copy.deepcopy(validated_data))
        self.create_ledger_entry(copy.deepcopy(validated_data), debit_instance)
        return debit_instance

    def update(self, instance, validated_data):
        # delete old instance first
        instance.delete()
        debit_instance = self.create_debit_entry(copy.deepcopy(validated_data))
        self.create_ledger_entry(copy.deepcopy(validated_data), debit_instance)
        return debit_instance


class ListRawDebitTransactionSerializer(serializers.ModelSerializer):
    class DebitLotSerializer(serializers.ModelSerializer):
        lot_detail = RawLotDetailsSerializer(many=True)

        class Meta:
            model = RawDebitLot
            fields = [
                "id",
                "lot_number",
                "lot_detail",
                "raw_product",
                "product_glue",
                "product_type",
            ]

    lots = DebitLotSerializer(many=True)

    class Meta:
        model = RawDebit
        fields = [
            "id",
            "person",
            "date",
            "serial",
            "manual_serial",
            "debit_type",
            "lots",
        ]


"""Raw Transfer Serializers"""


class RawTransferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawTransferLotDetail
        fields = [
            "id",
            "quantity",
            "actual_gazaana",
            "expected_gazaana",
            "warehouse",
            "transferring_warehouse",
            "raw_transfer_lot",
        ]
        read_only_fields = ["id", "lot_number", "raw_transfer_lot"]


class RawStockTransferSerializer(UniqueLotNumbers, serializers.ModelSerializer):
    class TransferLotSerializer(serializers.ModelSerializer):
        detail = RawTransferDetailSerializer(many=True, required=True)

        class Meta:
            model = RawTransferLot
            fields = ["raw_transfer", "lot_number", "detail"]
            read_only_fields = ["id", "raw_transfer"]

    data = TransferLotSerializer(many=True, required=True, write_only=True)

    class Meta:
        model = RawTransfer
        fields = [
            "id",
            "serial",
            "date",
            "data",
            "manual_serial",
        ]
        read_only_fields = ["id", "serial"]

    def validate(self, data):
        super().validate(data)
        for lot_idx, lot in enumerate(data["data"]):
            for det_idx, detail in enumerate(lot["detail"]):
                if detail["transferring_warehouse"] == detail["warehouse"]:
                    raise ValidationError(
                        f"Transfer warehouse and from warehouse are same in lot # {lot_idx + 1}, line {det_idx + 1}"
                    )
        return data

    def create_transfer_entry(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        transfer = RawTransfer.make_raw_transfer_transaction(
            copy.deepcopy(validated_data), branch, user
        )
        validated, error = validate_raw_inventory(branch)
        if not validated:
            raise ValidationError(error)
        return transfer

    def create(self, validated_data):
        transfer = self.create_transfer_entry(copy.deepcopy(validated_data))
        return transfer

    def update(self, instance, validated_data):
        # delete previous
        instance.delete()
        transfer = self.create_transfer_entry(copy.deepcopy(validated_data))
        return transfer


class ListRawTransferTransactionSerializer(serializers.ModelSerializer):
    class TransferLotSerializer(serializers.ModelSerializer):
        lot_detail = RawTransferDetailSerializer(many=True)

        class Meta:
            model = RawTransferLot
            fields = [
                "id",
                "lot_number",
                "lot_detail",
                "raw_product",
            ]

    lots = TransferLotSerializer(many=True)

    class Meta:
        model = RawTransfer
        fields = [
            "id",
            "date",
            "serial",
            "manual_serial",
            "lots",
        ]


"""Stock serializer"""


class ViewAllStockSerializer(serializers.Serializer):
    quantity = serializers.FloatField()
    actual_gazaana = serializers.FloatField()
    expected_gazaana = serializers.FloatField()
    lot_number = serializers.FloatField()
    raw_product = serializers.UUIDField()
    warehouse = serializers.UUIDField()


class RawTransactionLotAutofillSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawTransactionLot
        depth = 1
        fields = ["detail", "dying_number", "warehouse_number", "lot_detail"]
