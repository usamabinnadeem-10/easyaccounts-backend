from functools import reduce

from ledgers.models import Ledger
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import serializers, status
from rest_framework.exceptions import NotAcceptable

from .choices import TransactionTypes
from .models import (
    CancelledInvoice,
    CancelStockTransfer,
    StockTransfer,
    StockTransferDetail,
    Transaction,
    TransactionDetail,
)
from .utils import create_ledger_entries, create_ledger_string, update_stock


class ValidateTransactionSerial:
    """Validates the serial numbers for transactions"""

    last_serial_num = 0
    cancelled = None

    def validate(self, data):
        branch = self.context["request"].branch
        branch_filter = {"branch": branch}
        manual_serial_type = data["manual_serial_type"]
        manual_invoice_serial = data["manual_invoice_serial"]

        if Transaction.objects.filter(
            branch=branch,
            manual_invoice_serial=manual_invoice_serial,
            manual_serial_type=manual_serial_type,
        ).exists():
            raise serializers.ValidationError(
                "Invoice with that book number exists.", status.HTTP_400_BAD_REQUEST
            )

        self.last_serial_num = Transaction.get_next_serial(
            branch, "serial", manual_serial_type=manual_serial_type
        )

        max_from_cancelled = CancelledInvoice.get_next_serial(
            branch,
            "manual_invoice_serial",
            manual_serial_type=manual_serial_type,
        )
        max_from_transactions = Transaction.get_next_serial(
            branch,
            "manual_invoice_serial",
            manual_serial_type=manual_serial_type,
        )
        max_final = (
            max_from_cancelled
            if max_from_cancelled > max_from_transactions
            else max_from_transactions
        )

        if abs(max_final - manual_invoice_serial) > 1:
            raise NotAcceptable(f"Please use serial # {max_final}")

        try:
            self.cancelled = CancelledInvoice.objects.get(
                **branch_filter,
                manual_invoice_serial=manual_invoice_serial,
                manual_serial_type=manual_serial_type,
            )
        except Exception:
            pass

        if self.cancelled:
            raise NotAcceptable(
                f"Serial # {self.cancelled.manual_serial_type}-{self.cancelled.manual_invoice_serial} is cancelled"
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


class ValidateTotalAndSerial(ValidateTransactionSerial, ValidateTotal):
    """Validates transaction serial while editing"""

    def validate(self, data):
        data = self.validate_total(data)
        data = super().validate(data)
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


class TransactionSerializer(ValidateTotalAndSerial, serializers.ModelSerializer):
    """Transaction serializer for creating and viewing transactions"""

    category = ActivityCategory.TRANSACTION
    type = ActivityTypes.CREATED

    transaction_detail = TransactionDetailSerializer(many=True)
    paid = serializers.BooleanField(default=False)

    serial = serializers.ReadOnlyField()
    person_name = serializers.CharField(source="person.name", read_only=True)
    person_type = serializers.CharField(source="person.person_type", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "serial",
            "manual_invoice_serial",
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
            "person_name",
            "person_type",
            "manual_serial_type",
            "requires_action",
            "builty",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        request = self.context["request"]
        transaction_details = validated_data.pop("transaction_detail")
        paid = validated_data.pop("paid")
        branch_filter = {"branch": request.branch}
        user = request.user
        transaction = Transaction.objects.create(
            user=user, **branch_filter, **validated_data, serial=self.last_serial_num
        )
        details = []
        ledger_string = ""
        for detail in transaction_details:
            if TransactionDetail.is_rate_invalid(
                transaction.nature, detail["product"], detail["rate"]
            ):
                raise serializers.ValidationError(
                    f"Rate too low for {detail['product'].name}",
                    status.HTTP_400_BAD_REQUEST,
                )
            details.append(
                TransactionDetail(
                    transaction_id=transaction.id, **detail, **branch_filter
                )
            )
            ledger_string += create_ledger_string(detail)
            update_stock(transaction.nature, {**detail, **branch_filter})

        transactions = TransactionDetail.objects.bulk_create(details)
        ledger_data = create_ledger_entries(
            transaction,
            transaction_details,
            paid,
            ledger_string
            + f'{validated_data["detail"] if validated_data["detail"] else ""}',
        )
        Ledger.objects.bulk_create(ledger_data)
        validated_data["transaction_detail"] = transactions
        validated_data["id"] = transaction.id
        validated_data["serial"] = transaction.serial
        validated_data["date"] = transaction.date

        Log.create_log(
            self.type,
            self.category,
            f"{transaction.get_manual_serial()} ({transaction.get_type_display()}) for {transaction.person.name}",
            request,
        )

        return validated_data


class UpdateTransactionDetailSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(required=False)
    new = serializers.BooleanField(default=False, write_only=True)

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
            "new",
        ]
        read_only_fields = ["transaction"]


class UpdateTransactionSerializer(ValidateTotal, serializers.ModelSerializer):
    """Serializer for updating transaction"""

    category = ActivityCategory.TRANSACTION
    type = ActivityTypes.EDITED

    transaction_detail = UpdateTransactionDetailSerializer(many=True)
    serial = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "date",
            "serial",
            "type",
            "transaction_detail",
            "nature",
            "discount",
            "person",
            "account_type",
            "paid_amount",
            "detail",
            "manual_invoice_serial",
            "manual_serial_type",
            "requires_action",
            "builty",
        ]

    def validate(self, data):
        data = self.validate_total(data)
        return data

    def update(self, instance, validated_data):
        request = self.context["request"]
        transaction_detail = validated_data.pop("transaction_detail")
        branch = request.branch
        branch_filter = {"branch": branch}

        # check if user changed the book number
        if instance.manual_invoice_serial != validated_data["manual_invoice_serial"]:
            raise serializers.ValidationError(
                "You can not change book number while editing",
                status.HTTP_400_BAD_REQUEST,
            )

        # delete all the other transaction details
        # which were not in the transaction_detail
        all_transaction_details = TransactionDetail.objects.filter(
            **branch_filter, transaction=instance
        ).values("id", "product", "warehouse", "quantity", "yards_per_piece", "branch")
        ids_to_keep = []

        # make a list of transactions that should not be deleted
        for detail in transaction_detail:
            if not detail["new"]:
                ids_to_keep.append(detail["id"])

        # delete transaction detail rows that are not in ids_to_keep
        # and add stock of those products
        for transaction in all_transaction_details:
            if not transaction["id"] in ids_to_keep:
                to_delete = TransactionDetail.objects.get(
                    id=transaction["id"], **branch_filter
                )
                update_stock(
                    "C" if instance.nature == "D" else "D",
                    transaction,
                    instance.nature,
                )
                to_delete.delete()

        ledger_string = ""
        # for all the details, if it is new then create it otherwise edit the previous
        amount = 0.0
        for detail in transaction_detail:
            amount += detail["rate"] * detail["quantity"] * detail["yards_per_piece"]
            if TransactionDetail.is_rate_invalid(
                validated_data["nature"], detail["product"], detail["rate"]
            ):
                raise serializers.ValidationError(
                    f"Rate too low for {detail['product'].name}",
                    status.HTTP_400_BAD_REQUEST,
                )
            old_quantity = 0.0
            if detail["new"]:
                detail.pop("new")
                TransactionDetail.objects.create(
                    transaction=instance, **detail, **branch_filter
                )
            else:
                detail_instance = TransactionDetail.objects.get(
                    id=detail["id"], **branch_filter
                )
                old_quantity = detail_instance.quantity
                old_gazaana = detail_instance.yards_per_piece
                old_warehouse = detail_instance.warehouse
                old_product = detail_instance.product
                detail_instance.product = detail["product"]
                detail_instance.rate = detail["rate"]
                detail_instance.quantity = detail["quantity"]
                detail_instance.warehouse = detail["warehouse"]
                detail_instance.yards_per_piece = detail["yards_per_piece"]
                detail_instance.save()

            update_stock(
                validated_data.get("nature"),
                {**detail, "branch": branch},
                instance.nature,
                True,
                old_quantity,
                old_gazaana,
                old_product,
                old_warehouse,
            )

            ledger_string += create_ledger_string(detail)

        amount -= validated_data["discount"]
        ledger_instance = Ledger.objects.get(
            transaction=instance, account_type__isnull=True, **branch_filter
        )
        ledger_instance.detail = ledger_string + f'{validated_data["detail"]}\n'
        ledger_instance.nature = validated_data["nature"]
        ledger_instance.amount = amount
        ledger_instance.person = validated_data["person"]
        if validated_data.get("date", None):
            ledger_instance.date = validated_data["date"]
        ledger_instance.save()

        account_type = (
            validated_data["account_type"] if "account_type" in validated_data else None
        )
        paid_amount = (
            validated_data["paid_amount"] if "paid_amount" in validated_data else None
        )

        PAID = TransactionTypes.PAID
        # if the transaction was unpaid before and is now paid then create a new ledger entry
        if validated_data["type"] != instance.type and validated_data["type"] == PAID:
            Ledger.objects.create(
                **{
                    "detail": f"Paid on {account_type.name}",
                    "amount": paid_amount,
                    "transaction": instance,
                    "nature": "C",
                    "account_type": account_type,
                    "person": instance.person,
                    "date": instance.date,
                    "branch": instance.branch,
                }
            )

        # if transaction was paid and is now unpaid then delete the old ledger entry
        if instance.type == PAID and validated_data["type"] != PAID:
            paid_instance = Ledger.objects.get(
                transaction=instance,
                account_type__isnull=False,
                **branch_filter,
            )
            paid_instance.delete()

        # if both types are paid then update the Ledger entry
        if instance.type == PAID and validated_data["type"] == instance.type:
            paid_instance = Ledger.objects.get(
                transaction=instance,
                account_type__isnull=False,
                **branch_filter,
            )
            paid_instance.amount = validated_data["paid_amount"]
            paid_instance.account_type = validated_data["account_type"]
            paid_instance.detail = f'Paid on {validated_data["account_type"].name}'
            paid_instance.person = validated_data["person"]
            if validated_data["date"]:
                paid_instance.date = validated_data["date"]
            paid_instance.save()

        Log.create_log(
            self.type,
            self.category,
            f"{instance.manual_serial_type}-{instance.manual_invoice_serial} ({instance.get_type_display()}) for {instance.person.name}",
            request,
        )

        return super().update(instance, validated_data)


class CancelledInvoiceSerializer(ValidateTransactionSerial, serializers.ModelSerializer):

    request = None
    type = ActivityTypes.CREATED
    category = ActivityCategory.CANCELLED_TRANSACTION

    class Meta:
        model = CancelledInvoice
        fields = [
            "id",
            "manual_invoice_serial",
            "manual_serial_type",
            "comment",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        self.request = self.context["request"]
        if CancelledInvoice.objects.filter(
            branch=self.request.branch,
            manual_invoice_serial=data["manual_invoice_serial"],
            manual_serial_type=data["manual_serial_type"],
        ).exists():
            raise serializers.ValidationError(
                "Invoice with that book number is already cancelled.", 400
            )
        data = super().validate(data)
        return data

    def create(self, validated_data):
        serial = None
        branch = self.request.branch
        user = self.request.user
        try:
            serial = Transaction.objects.get(
                branch=branch,
                manual_invoice_serial=validated_data["manual_invoice_serial"],
                manual_serial_type=validated_data["manual_serial_type"],
            )
        except Exception:
            pass

        if not serial:
            validated_data["branch"] = branch
            validated_data["user"] = user
            instance = super().create(validated_data)
            Log.create_log(
                self.type,
                self.category,
                f"{instance.get_manual_serial()}",
                self.request,
            )
            return instance
        else:
            raise NotAcceptable(
                f"{serial.manual_invoice_serial} is already used in transaction ID # {serial.serial}",
                400,
            )


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
            "manual_invoice_serial",
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
        next_manual = StockTransfer.get_next_serial(
            branch, "manual_invoice_serial", from_warehouse=data["from_warehouse"]
        )
        next_cancel = CancelStockTransfer.get_next_serial(
            branch, "manual_invoice_serial", warehouse=data["from_warehouse"]
        )
        final_serial = max(next_manual, next_cancel)
        if data["manual_invoice_serial"] != final_serial:
            raise serializers.ValidationError(f"Please use receipt # {final_serial}")
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
                branch, "serial", from_warehouse=from_warehouse
            ),
            branch=branch,
        )
        detail_entries = []
        total_quantity = 0
        for detail in transfer_detail:
            total_quantity += detail["quantity"]
            data = {
                "product": detail["product"],
                "warehouse": from_warehouse,
                "yards_per_piece": detail["yards_per_piece"],
                "quantity": detail["quantity"],
                "branch": branch,
            }
            update_stock("D", data)
            data.update({"warehouse": detail["to_warehouse"]})
            update_stock("C", data)

            detail_entries.append(
                StockTransferDetail(
                    branch=branch,
                    transfer=transfer_instance,
                    **detail,
                )
            )
        StockTransferDetail.objects.bulk_create(detail_entries)

        Log.create_log(
            self.type,
            self.category,
            f"{total_quantity} thaan from {transfer_instance.from_warehouse.name}, serial # {transfer_instance.manual_invoice_serial}",
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
            "manual_invoice_serial",
            "from_warehouse",
            "transfer_detail",
        ]


class CancelStockTransferSerializer(serializers.ModelSerializer):

    request = None
    type = ActivityTypes.CREATED
    category = ActivityCategory.CANCELLED_STOCK_TRANSFER

    class Meta:
        model = CancelStockTransfer
        fields = ["id", "warehouse", "manual_invoice_serial"]
        read_only_fields = ["id"]

    def validate(self, data):
        self.request = self.context["request"]
        branch = self.request.branch
        from_warehouse = data["warehouse"]
        serial = data["manual_invoice_serial"]
        if StockTransfer.objects.filter(
            branch=branch,
            from_warehouse=from_warehouse,
            manual_invoice_serial=serial,
        ).exists():
            raise serializers.ValidationError(
                "This serial is already in use", status.HTTP_400_BAD_REQUEST
            )

        if CancelStockTransfer.objects.filter(
            branch=branch,
            warehouse=from_warehouse,
            manual_invoice_serial=serial,
        ).exists():
            raise serializers.ValidationError(
                "This serial is already cancelled", status.HTTP_400_BAD_REQUEST
            )

        next_serial = StockTransfer.get_next_serial(
            branch, "manual_invoice_serial", from_warehouse=from_warehouse
        )
        next_cancel = CancelStockTransfer.get_next_serial(
            branch, "manual_invoice_serial", warehouse=from_warehouse
        )
        final_serial = max(next_serial, next_cancel)
        if serial > final_serial:
            raise serializers.ValidationError(
                "You can not cancel future serial", status.HTTP_400_BAD_REQUEST
            )

        return data

    def create(self, validated_data):
        validated_data["branch"] = self.request.branch
        instance = super().create(validated_data)

        Log.create_log(
            self.type,
            self.category,
            f"serial # {instance.manual_invoice_serial} of {instance.warehouse.name}",
            self.request,
        )

        return instance
