from functools import reduce

from rest_framework import serializers, status

from cheques.utils import get_cheque_account
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .choices import TransactionSerialTypes
from .models import StockTransfer, StockTransferDetail, Transaction, TransactionDetail


class ValidateSerial:
    """Validates if manual serial is unique for branch"""

    def validate_serial(self, data):
        if data["manual_serial"]:
            if Transaction.objects.filter(
                manual_serial=data["manual_serial"],
                person__branch=self.context["request"].branch,
                serial_type=data["serial_type"],
            ).exists():
                if data["is_cancelled"]:
                    raise serializers.ValidationError(
                        "This serial is already cancelled", status.HTTP_400_BAD_REQUEST
                    )
                raise serializers.ValidationError(
                    "This serial already exists", status.HTTP_400_BAD_REQUEST
                )
        if data["wasooli_number"]:
            if data["serial_type"] != TransactionSerialTypes.SUP:
                raise serializers.ValidationError(
                    "Wasooli number can not be added with this transaction type",
                    status.HTTP_400_BAD_REQUEST,
                )
            if Transaction.objects.filter(
                wasooli_number=data["wasooli_number"],
                person__branch=self.context["request"].branch,
                serial_type=data["serial_type"],
            ).exists():
                raise serializers.ValidationError(
                    "This wasooli number already exists", status.HTTP_400_BAD_REQUEST
                )
        return data


class ValidateTotal:
    """Validates total for transaction"""

    def validate_total(self, data):
        if not data["is_cancelled"]:
            total = reduce(
                lambda prev, curr: prev
                + (curr["rate"] * curr["quantity"] * curr["yards_per_piece"]),
                data["transaction_detail"],
                0,
            )
            total -= data["discount"]
            if total <= 0:
                raise serializers.ValidationError(
                    "Total is too low", status.HTTP_400_BAD_REQUEST
                )
            if data["paid"]:
                if data["paid_amount"] > total:
                    raise serializers.ValidationError(
                        "Paid amount can not be greater than total",
                        status.HTTP_400_BAD_REQUEST,
                    )
        return data


class ValidateAccountType:
    """Validates if the account type is not cheque account for transaction"""

    def validate_account(self, data):
        if data["paid"]:
            if (
                data["account_type"]
                == get_cheque_account(self.context["request"].branch).account
            ):
                raise serializers.ValidationError(
                    "Please use another account type for transaction",
                    status.HTTP_400_BAD_REQUEST,
                )
        else:
            if data.get("account_type", False) or data.get("paid_amount", None):
                raise serializers.ValidationError(
                    "Please remove account type / paid amount",
                    status.HTTP_400_BAD_REQUEST,
                )
        return data


class ValidateTransaction(
    ValidateAccountType,
    ValidateSerial,
    ValidateTotal,
):
    """Validates transaction serial, account_type and total"""

    def validate(self, data):
        data = self.validate_total(data)
        data = self.validate_serial(data)
        data = self.validate_account(data)

        return data


class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = [
            "id",
            "transaction",
            "product",
            "rate",
            "yards_per_piece",
            "quantity",
            "warehouse",
        ]
        read_only_fields = ["id", "transaction"]
        ordering = ["product__name"]


class TransactionSerializer(
    ValidateTransaction,
    serializers.ModelSerializer,
):
    """Transaction serializer for creating and viewing transactions"""

    category = ActivityCategory.TRANSACTION
    type = ActivityTypes.CREATED
    transaction_detail = TransactionDetailSerializer(many=True)
    paid = serializers.BooleanField(default=False)
    serial = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "serial",
            "manual_serial",
            "wasooli_number",
            "date",
            "transaction_detail",
            "nature",
            "type",
            "discount",
            "person",
            "paid",
            "account_type",
            "paid_amount",
            "detail",
            "serial_type",
            "requires_action",
            "builty",
            "is_cancelled",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        request = self.context["request"]
        transaction = None
        t_detail = None
        instance = Transaction.make_transaction(validated_data, request)

        transaction = instance["transaction"]
        t_detail = instance["detail"]
        validated_data["transaction_detail"] = t_detail
        validated_data["id"] = transaction.id
        validated_data["serial"] = transaction.serial
        validated_data["date"] = transaction.date

        Log.create_log(
            self.type,
            self.category,
            f"{transaction.get_computer_serial()} ({transaction.get_type_display()}) for {transaction.person.name}",
            request,
        )

        return validated_data


class UpdateTransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = [
            "transaction",
            "product",
            "rate",
            "yards_per_piece",
            "quantity",
            "warehouse",
        ]
        read_only_fields = ["transaction"]


class UpdateTransactionSerializer(
    ValidateAccountType, ValidateTotal, serializers.ModelSerializer
):
    """Serializer for updating transaction"""

    category = ActivityCategory.TRANSACTION
    type = ActivityTypes.EDITED

    transaction_detail = UpdateTransactionDetailSerializer(many=True)
    serial = serializers.ReadOnlyField()
    paid = serializers.BooleanField(default=False)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "date",
            "serial",
            "type",
            "transaction_detail",
            "paid",
            "nature",
            "discount",
            "person",
            "account_type",
            "paid_amount",
            "detail",
            "manual_serial",
            "wasooli_number",
            # "manual_serial_type",
            "serial_type",
            "requires_action",
            "builty",
            "is_cancelled",
        ]

    def validate(self, data):
        data = self.validate_total(data)
        data = self.validate_account(data)
        return data

    def update(self, instance, validated_data):
        request = self.context["request"]
        # transaction_detail = validated_data.pop("transaction_detail")
        # check if user changed the book number
        # if he did, then ensure it does not exist already
        if instance.manual_serial != validated_data["manual_serial"]:
            if Transaction.objects.filter(
                manual_serial=validated_data["manual_serial"],
                person__branch=request.branch,
            ).exists():
                raise serializers.ValidationError(
                    "This serial already exists",
                    status.HTTP_400_BAD_REQUEST,
                )
        if instance.wasooli_number != validated_data["wasooli_number"]:
            if Transaction.objects.filter(
                wasooli_number=validated_data["wasooli_number"],
                person__branch=request.branch,
            ).exists():
                raise serializers.ValidationError(
                    "This wasooli number already exists",
                    status.HTTP_400_BAD_REQUEST,
                )
        transaction = Transaction.make_transaction(validated_data, request, instance)

        Log.create_log(
            self.type,
            self.category,
            # f"{instance.manual_serial_type}-{instance.manual_invoice_serial} ({instance.get_type_display()}) for {instance.person.name}",
            f"{instance.serial_type}-{instance.serial} ({instance.get_type_display()}) for {instance.person.name}",
            request,
        )

        validated_data["transaction_detail"] = transaction["detail"]
        validated_data["id"] = transaction["transaction"].id
        validated_data["serial"] = transaction["transaction"].serial
        validated_data["date"] = transaction["transaction"].date
        return validated_data


class TransferStockDetail(serializers.ModelSerializer):
    class Meta:
        model = StockTransferDetail
        fields = [
            "id",
            "product",
            "yards_per_piece",
            "to_warehouse",
            "quantity",
        ]
        read_only_fields = ["id"]


class TransferStockSerializer(serializers.ModelSerializer):

    request = None
    type = ActivityTypes.CREATED
    category = ActivityCategory.STOCK_TRANSFER
    transfer_detail = TransferStockDetail(many=True, required=True)

    class Meta:
        model = StockTransfer
        fields = [
            "id",
            "date",
            "serial",
            "transfer_detail",
            "from_warehouse",
            "manual_serial",
        ]
        read_only_fields = ["id", "serial"]

    def validate(self, data):
        self.request = self.context["request"]
        branch = self.request.branch
        from_warehouse = data["from_warehouse"]
        for row in data["transfer_detail"]:
            if from_warehouse == row["to_warehouse"]:
                raise serializers.ValidationError(
                    "You are trying to transfer to same warehouse product is in",
                    status.HTTP_400_BAD_REQUEST,
                )

        if StockTransfer.objects.filter(
            manual_serial=data["manual_serial"],
            from_warehouse__branch=branch,
            from_warehouse=data["from_warehouse"],
        ).exists():
            raise serializers.ValidationError(f"Serial # {data['manual_serial']} exists")

        return data

    def create(self, validated_data):
        data = StockTransfer.make_transfer(validated_data, self.request)
        transfer_detail = data["transfer_detail"]
        transfer_instance = data["transfer"]
        validated_data["transfer_detail"] = transfer_detail
        validated_data["serial"] = transfer_instance.serial
        validated_data["id"] = transfer_instance.id
        validated_data["date"] = transfer_instance.date

        Log.create_log(
            self.type,
            self.category,
            f"T-{transfer_instance.serial}:\n{data['total']} thaan from {transfer_instance.from_warehouse.name} on {transfer_instance.date}",
            self.request,
        )

        return validated_data


class UpdateTransferStockSerializer(serializers.ModelSerializer):
    request = None
    type = ActivityTypes.EDITED
    category = ActivityCategory.STOCK_TRANSFER
    transfer_detail = TransferStockDetail(many=True, required=True)

    class Meta:
        model = StockTransfer
        fields = [
            "id",
            "date",
            "serial",
            "transfer_detail",
            "from_warehouse",
            "manual_serial",
        ]
        read_only_fields = ["id", "serial"]

    def validate(self, data):
        self.request = self.context["request"]
        from_warehouse = data["from_warehouse"]
        for row in data["transfer_detail"]:
            if from_warehouse == row["to_warehouse"]:
                raise serializers.ValidationError(
                    "You are trying to transfer to same warehouse product is in",
                    status.HTTP_400_BAD_REQUEST,
                )
        return data

    def update(self, instance, validated_data):

        if instance.manual_serial != validated_data["manual_serial"]:
            if StockTransfer.objects.filter(
                from_warehouse__branch=self.request.branch,
                from_warehouse=validated_data["from_warehouse"],
                manual_serial=validated_data["manual_serial"],
            ).exists():
                raise serializers.ValidationError(
                    f"Serial {validated_data['manual_serial']} already exists",
                    status.HTTP_400_BAD_REQUEST,
                )

        data = StockTransfer.make_transfer(validated_data, self.request, instance)
        transfer_detail = data["transfer_detail"]
        transfer_instance = data["transfer"]

        validated_data["transfer_detail"] = transfer_detail
        validated_data["serial"] = transfer_instance.serial
        validated_data["id"] = transfer_instance.id
        validated_data["date"] = transfer_instance.date

        Log.create_log(
            self.type,
            self.category,
            f"T-{transfer_instance.serial}:\n{data['total']} thaan from {transfer_instance.from_warehouse.name} on {transfer_instance.date}",
            self.request,
        )

        return validated_data


class ViewTransfersSerializer(serializers.ModelSerializer):
    class Serializer(serializers.ModelSerializer):
        class Meta:
            model = StockTransferDetail
            fields = "__all__"

    transfer_detail = Serializer(many=True)

    class Meta:
        model = StockTransfer
        fields = [
            "id",
            "date",
            "serial",
            "manual_serial",
            "from_warehouse",
            "transfer_detail",
        ]


class GetAllStockSerializer(serializers.Serializer):

    product = serializers.UUIDField(read_only=True)
    warehouse = serializers.UUIDField(read_only=True)
    yards_per_piece = serializers.FloatField(read_only=True)
    quantity = serializers.FloatField(read_only=True)
