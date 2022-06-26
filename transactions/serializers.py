from functools import reduce

from cheques.utils import get_cheque_account
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import serializers, status
from rest_framework.exceptions import NotAcceptable

from .models import (  # CancelledInvoice,; CancelStockTransfer,
    StockTransfer,
    StockTransferDetail,
    Transaction,
    TransactionDetail,
)

# class ValidateTransactionSerial:
#     """Validates the serial numbers for transactions"""

#     last_serial_num = 0
#     cancelled = None

#     def validate_serial(self, data):
#         branch = self.context["request"].branch
#         branch_filter = {"branch": branch}
#         manual_serial_type = data["manual_serial_type"]
#         manual_invoice_serial = data["manual_invoice_serial"]

#         if Transaction.objects.filter(
#             person__branch=branch,
#             manual_invoice_serial=manual_invoice_serial,
#             manual_serial_type=manual_serial_type,
#         ).exists():
#             raise serializers.ValidationError(
#                 "Invoice with that book number exists.", status.HTTP_400_BAD_REQUEST
#             )

#         self.last_serial_num = Transaction.get_next_serial(
#             "serial", manual_serial_type=manual_serial_type, person__branch=branch
#         )

#         max_from_cancelled = CancelledInvoice.get_next_serial(
#             "manual_invoice_serial",
#             manual_serial_type=manual_serial_type,
#             branch=branch,
#         )
#         max_from_transactions = Transaction.get_next_serial(
#             "manual_invoice_serial",
#             manual_serial_type=manual_serial_type,
#             person__branch=branch,
#         )
#         max_final = (
#             max_from_cancelled
#             if max_from_cancelled > max_from_transactions
#             else max_from_transactions
#         )

#         if abs(max_final - manual_invoice_serial) > 1:
#             raise NotAcceptable(f"Please use serial # {max_final}")

#         try:
#             self.cancelled = CancelledInvoice.objects.get(
#                 **branch_filter,
#                 manual_invoice_serial=manual_invoice_serial,
#                 manual_serial_type=manual_serial_type,
#             )
#         except Exception:
#             pass

#         if self.cancelled:
#             raise NotAcceptable(
#                 f"Serial # {self.cancelled.manual_serial_type}-{self.cancelled.manual_invoice_serial} is cancelled"
#             )

#         return data


class ValidateSerial:
    """Validates if manual serial is unique for branch"""

    def validate_serial(self, data):
        if data["manual_serial"]:
            if Transaction.objects.filter(
                manual_serial=data["manual_serial"],
                person__branch=self.context["request"].branch,
            ).exists():
                raise serializers.ValidationError(
                    "This serial already exists", status.HTTP_400_BAD_REQUEST
                )
        return data


class ValidateTotal:
    """Validates total for transaction"""

    def validate_total(self, data):
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
            # "manual_serial_type",
            "serial_type",
            "requires_action",
            "builty",
        ]

    def validate(self, data):
        data = self.validate_total(data)
        data = self.validate_account(data)
        return data

    def update(self, instance, validated_data):
        request = self.context["request"]
        # transaction_detail = validated_data.pop("transaction_detail")
        branch = request.branch
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


# class CancelledInvoiceSerializer(
#     # ValidateTransactionSerial,
#     serializers.ModelSerializer):

#     request = None
#     type = ActivityTypes.CREATED
#     category = ActivityCategory.CANCELLED_TRANSACTION

#     class Meta:
#         model = CancelledInvoice
#         fields = [
#             "id",
#             # "manual_invoice_serial",
#             # "manual_serial_type",
#             "serial_type",
#             "comment",
#         ]
#         read_only_fields = ["id"]

#     def validate(self, data):
#         self.request = self.context["request"]
#         if CancelledInvoice.objects.filter(
#             branch=self.request.branch,
#             manual_invoice_serial=data["manual_invoice_serial"],
#             manual_serial_type=data["manual_serial_type"],
#         ).exists():
#             raise serializers.ValidationError(
#                 "Invoice with that book number is already cancelled.", 400
#             )
#         data = super().validate(data)
#         return data

#     def create(self, validated_data):
#         serial = None
#         branch = self.request.branch
#         user = self.request.user
#         try:
#             serial = Transaction.objects.get(
#                 person__branch=branch,
#                 manual_invoice_serial=validated_data["manual_invoice_serial"],
#                 manual_serial_type=validated_data["manual_serial_type"],
#             )
#         except Exception:
#             pass

#         if not serial:
#             validated_data["branch"] = branch
#             validated_data["user"] = user
#             instance = super().create(validated_data)
#             Log.create_log(
#                 self.type,
#                 self.category,
#                 f"{instance.get_manual_serial()}",
#                 self.request,
#             )
#             return instance
#         else:
#             raise NotAcceptable(
#                 f"{serial.manual_invoice_serial} is already used in transaction ID # {serial.serial}",
#                 400,
#             )


class TransferStockDetail(serializers.ModelSerializer):
    class Meta:
        model = StockTransferDetail
        fields = [
            "product",
            "yards_per_piece",
            "to_warehouse",
            "quantity",
        ]


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
            # "manual_invoice_serial",
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
        # next_manual = StockTransfer.get_next_serial(
        #     "manual_invoice_serial", from_warehouse=data["from_warehouse"], branch=branch
        # )
        # next_cancel = CancelStockTransfer.get_next_serial(
        #     "manual_invoice_serial",
        #     warehouse=data["from_warehouse"],
        #     warehouse__branch=branch,
        # )
        # final_serial = max(next_manual, next_cancel)
        # if data["manual_invoice_serial"] != final_serial:
        #     raise serializers.ValidationError(f"Please use receipt # {final_serial}")
        return data

    def create(self, validated_data):
        branch = self.request.branch
        user = self.request.user
        transfer_detail = validated_data.pop("transfer_detail")
        from_warehouse = validated_data["from_warehouse"]
        transfer_instance = StockTransfer.objects.create(
            **validated_data,
            user=user,
            serial=StockTransfer.get_next_serial(
                "serial", from_warehouse=from_warehouse, branch=branch
            ),
            branch=branch,
        )
        detail_entries = []
        total_quantity = reduce(
            lambda prev, curr: prev + curr["quantity"], transfer_detail, 0
        )
        for detail in transfer_detail:
            detail_entries.append(
                StockTransferDetail(
                    transfer=transfer_instance,
                    **detail,
                )
            )
        StockTransferDetail.objects.bulk_create(detail_entries)
        Transaction.check_stock(branch, None)

        Log.create_log(
            self.type,
            self.category,
            f"{total_quantity} thaan from {transfer_instance.from_warehouse.name}, serial # {transfer_instance.serial}",
            self.request,
        )

        validated_data["transfer_detail"] = transfer_detail
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
            # "manual_invoice_serial",
            "from_warehouse",
            "transfer_detail",
        ]


# class CancelStockTransferSerializer(serializers.ModelSerializer):

#     request = None
#     type = ActivityTypes.CREATED
#     category = ActivityCategory.CANCELLED_STOCK_TRANSFER

#     class Meta:
#         model = CancelStockTransfer
#         fields = ["id", "warehouse", "manual_invoice_serial"]
#         read_only_fields = ["id"]

#     def validate(self, data):
#         self.request = self.context["request"]
#         branch = self.request.branch
#         from_warehouse = data["warehouse"]
#         serial = data["manual_invoice_serial"]
#         if StockTransfer.objects.filter(
#             branch=branch,
#             from_warehouse=from_warehouse,
#             manual_invoice_serial=serial,
#         ).exists():
#             raise serializers.ValidationError(
#                 "This serial is already in use", status.HTTP_400_BAD_REQUEST
#             )

#         if CancelStockTransfer.objects.filter(
#             warehouse__branch=branch,
#             warehouse=from_warehouse,
#             manual_invoice_serial=serial,
#         ).exists():
#             raise serializers.ValidationError(
#                 "This serial is already cancelled", status.HTTP_400_BAD_REQUEST
#             )

#         next_serial = StockTransfer.get_next_serial(
#             "manual_invoice_serial", from_warehouse=from_warehouse, branch=branch
#         )
#         next_cancel = CancelStockTransfer.get_next_serial(
#             "manual_invoice_serial", warehouse=from_warehouse, warehouse__branch=branch
#         )
#         final_serial = max(next_serial, next_cancel)
#         if serial > final_serial:
#             raise serializers.ValidationError(
#                 "You can not cancel future serial", status.HTTP_400_BAD_REQUEST
#             )

#         return data

#     def create(self, validated_data):
#         validated_data["branch"] = self.request.branch
#         instance = super().create(validated_data)

#         Log.create_log(
#             self.type,
#             self.category,
#             f"serial # {instance.manual_invoice_serial} of {instance.warehouse.name}",
#             self.request,
#         )

#         return instance


class GetAllStockSerializer(serializers.Serializer):

    product = serializers.UUIDField(read_only=True)
    warehouse = serializers.UUIDField(read_only=True)
    yards_per_piece = serializers.FloatField(read_only=True)
    quantity = serializers.FloatField(read_only=True)
