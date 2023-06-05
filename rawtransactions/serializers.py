import copy
from functools import reduce

from django.forms import model_to_dict
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from essentials.choices import PersonChoices
from ledgers.models import LedgerAndRawDebit, LedgerAndRawTransaction
from transactions.choices import TransactionChoices

from .choices import RawDebitTypes
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
from .utils import get_all_raw_stock, get_current_stock_position, is_array_unique


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
            "rate_gazaana",
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
            "detail",
            "dying_number",
            "warehouse_number",
        ]
        read_only_fields = [
            "id",
            "lot_number",
            "raw_transaction",
        ]


class CreateRawTransactionSerializer(serializers.ModelSerializer):
    lots = RawTransactionLotSerializer(many=True, required=True, write_only=True)

    class Meta:
        model = RawTransaction
        fields = ["id", "person", "date", "manual_serial", "lots"]
        read_only_fields = [
            "id",
        ]

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

    def validate_person_and_raw_product(self, transaction_data):
        """validates if raw product belongs to person for raw transaction"""
        person = transaction_data["person"]
        lots = transaction_data["lots"]
        for index, lot in enumerate(lots):
            raw_product = lot["raw_product"]
            if raw_product.person.id != person.id:
                raise serializers.ValidationError(
                    f"This product does not belong to supplier lot # {index + 1}",
                    status.HTTP_400_BAD_REQUEST,
                )

    def validate(self, data):
        self.validate_warehouse_and_lot_issued(data)
        self.validate_person_and_raw_product(data)
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
                        # and val["formula"] == detail["formula"].id
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

    def validate_inventory(self, branch):
        stock = get_current_stock_position(branch)
        for s in stock:
            if s["quantity"] < 0:
                return False

        return True


class RawDebitSerializer(UniqueLotNumbers, StockCheck, serializers.ModelSerializer):
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

    def create(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        check_person = (
            True if validated_data["debit_type"] == RawDebitTypes.RETURN else False
        )
        person = validated_data["person"] if check_person else None
        self.check_stock(validated_data["data"], check_person, person)

        debit_instance = RawDebit.make_raw_debit_transaction(
            copy.deepcopy(validated_data), branch, user
        )

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

        return debit_instance


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

    rawtransactionlot_set = LotSerializer(many=True)

    class Meta:
        model = RawTransaction
        fields = [
            "id",
            "person",
            "date",
            "serial",
            "date",
            "rawtransactionlot_set",
        ]


class ViewAllStockSerializer(serializers.Serializer):
    quantity = serializers.FloatField()
    actual_gazaana = serializers.FloatField()
    expected_gazaana = serializers.FloatField()
    raw_product = serializers.UUIDField()
    warehouse = serializers.UUIDField()
    # formula = serializers.UUIDField()
    # nature = serializers.CharField()


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


class RawStockTransferSerializer(
    UniqueLotNumbers, StockCheck, serializers.ModelSerializer
):
    class TransferLotSerializer(serializers.ModelSerializer):
        detail = RawTransferDetailSerializer(many=True, required=True)

        class Meta:
            model = RawTransferLot
            fields = ["raw_transfer", "lot_number", "detail"]
            read_only_fields = ["id", "raw_transfer"]

    data = TransferLotSerializer(many=True, required=True)

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
        # if not RawDebit.is_serial_unique(
        #     manual_invoice_serial=data["manual_invoice_serial"],
        #     debit_type=data["debit_type"],
        #     branch=self.context["request"].branch,
        # ):
        #     raise ValidationError(f"Serial # {data['manual_invoice_serial']} exists")

        return data

    def create(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        RawTransfer.make_raw_transfer_transaction(
            copy.deepcopy(validated_data), branch, user
        )
        if not self.validate_inventory(branch):
            raise ValidationError("Low stock")
        return validated_data


class ListRawDebitTransactionSerializer(serializers.ModelSerializer):
    class DebitLotSerializer(serializers.ModelSerializer):
        rawdebitlotdetail_set = RawLotDetailsSerializer(many=True)
        raw_product = serializers.SerializerMethodField()

        class Meta:
            model = RawDebitLot
            fields = ["id", "lot_number", "rawdebitlotdetail_set", "raw_product"]

        def get_raw_product(self, obj):
            return model_to_dict(obj.lot_number.raw_product)

    rawdebitlot_set = DebitLotSerializer(many=True)

    class Meta:
        model = RawDebit
        fields = [
            "id",
            "person",
            "date",
            "serial",
            "manual_serial",
            "debit_type",
            "rawdebitlot_set",
        ]


class ListRawTransferTransactionSerializer(serializers.ModelSerializer):
    class TransferLotSerializer(serializers.ModelSerializer):
        rawtransferlotdetail_set = RawTransferDetailSerializer(many=True)
        raw_product = serializers.SerializerMethodField()

        class Meta:
            model = RawTransferLot
            fields = [
                "id",
                "lot_number",
                "rawtransferlotdetail_set",
                "raw_product",
            ]

        def get_raw_product(self, obj):
            return model_to_dict(obj.lot_number.raw_product)

    rawtransferlot_set = TransferLotSerializer(many=True)

    class Meta:
        model = RawTransfer
        fields = [
            "id",
            "date",
            "serial",
            "manual_serial",
            "rawtransferlot_set",
        ]


class UpdateRawTransactionSerializer(serializers.ModelSerializer):
    class UpdateRawTransactionLotSerializer(serializers.ModelSerializer):
        class UpdateRawLotDetailsSerializer(serializers.ModelSerializer):
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
                # read_only_fields = ["id", "lot_number"]

        lot_detail = UpdateRawLotDetailsSerializer(many=True)
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
                "detail",
                "dying_number",
                "warehouse_number",
            ]
            # read_only_fields = [
            #     "id",
            # ]
            extra_kwargs = {"id": {"required": False, "allow_null": True}}

    lots = UpdateRawTransactionLotSerializer(many=True, required=True)

    class Meta:
        model = RawTransaction
        fields = ["id", "person", "date", "manual_serial", "lots"]
        # read_only_fields = [
        #     "id",
        # ]

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

    def validate_person_and_raw_product(self, transaction_data):
        """validates if raw product belongs to person for raw transaction"""
        person = transaction_data["person"]
        lots = transaction_data["lots"]
        for index, lot in enumerate(lots):
            raw_product = lot["raw_product"]
            if raw_product.person.id != person.id:
                raise serializers.ValidationError(
                    f"This product does not belong to supplier lot # {index + 1}",
                    status.HTTP_400_BAD_REQUEST,
                )

    def validate(self, data):
        self.validate_warehouse_and_lot_issued(data)
        self.validate_person_and_raw_product(data)
        return data

    def update(self, instance, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user

        lot_ids_to_create = list(
            filter(lambda lot: not lot["id"], validated_data["lots"])
        )
        new_lots_ids = list(map(lambda lot: lot["id"] or "", validated_data["lots"]))
        old_lots = RawTransactionLot.objects.filter(raw_transaction=instance)

        # delete lots which are not present in new data
        for lot in old_lots:
            if lot.id not in new_lots_ids:
                try:
                    lot.delete()
                except Exception as e:
                    print(e)

        bulk_create_new_lots = []
        # create new lots
        for new_lot in lot_ids_to_create:
            bulk_create_new_lots.append(RawTransactionLot())

        new_lots = validated_data["lots"]
        validated_data_copy = copy.deepcopy(validated_data)

        # raw_transaction = RawTransaction.make_raw_transaction(
        #     copy.deepcopy(validated_data), branch, user
        # )
        # LedgerAndRawTransaction.create_ledger_entry(
        #     raw_transaction,
        #     RawTransaction.get_raw_transaction_total(validated_data),
        #     user,
        # )

        return validated_data
