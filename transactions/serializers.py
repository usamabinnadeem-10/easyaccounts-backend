from django.db.models import Max
from essentials.models import Stock, Warehouse
from ledgers.models import Ledger
from rawtransactions.utils import is_array_unique
from rest_framework import serializers, status
from rest_framework.exceptions import NotAcceptable

from .choices import TransactionTypes
from .models import (
    CancelledInvoice,
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
        if Transaction.objects.filter(
            branch=branch,
            manual_invoice_serial=data["manual_invoice_serial"],
            manual_serial_type=data["manual_serial_type"],
        ).exists():
            raise serializers.ValidationError(
                "Invoice with that book number exists.", status.HTTP_400_BAD_REQUEST
            )

        self.last_serial_num = (
            Transaction.objects.filter(**branch_filter).aggregate(Max("serial"))[
                "serial__max"
            ]
            or 0
        )

        data["manual_invoice_serial"]
        max_from_cancelled = (
            CancelledInvoice.objects.filter(
                **branch_filter,
                manual_serial_type=data["manual_serial_type"],
            ).aggregate(Max("manual_invoice_serial"))["manual_invoice_serial__max"]
            or 0
        )
        max_from_transactions = (
            Transaction.objects.filter(
                **branch_filter,
                manual_serial_type=data["manual_serial_type"],
            ).aggregate(Max("manual_invoice_serial"))["manual_invoice_serial__max"]
            or 0
        )
        max_final = (
            max_from_cancelled
            if max_from_cancelled > max_from_transactions
            else max_from_transactions
        )

        if abs(max_final - data["manual_invoice_serial"]) > 1:
            raise NotAcceptable(f"Please use serial # {max_final + 1}")

        try:
            self.cancelled = CancelledInvoice.objects.get(
                **branch_filter,
                manual_invoice_serial=data["manual_invoice_serial"],
                manual_serial_type=data["manual_serial_type"],
            )
        except Exception:
            pass

        if self.cancelled:
            raise NotAcceptable(
                f"Serial # {self.cancelled.manual_serial_type}-{self.cancelled.manual_invoice_serial} is cancelled"
            )

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
            "amount",
        ]
        read_only_fields = ["id", "transaction"]


class TransactionSerializer(ValidateTransactionSerial, serializers.ModelSerializer):

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
            "draft",
            "paid",
            "account_type",
            "paid_amount",
            "detail",
            "person_name",
            "person_type",
            "manual_serial_type",
            "requires_action",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        transaction_details = validated_data.pop("transaction_detail")
        paid = validated_data.pop("paid")
        branch_filter = {"branch": self.context["request"].branch}
        transaction = Transaction.objects.create(
            **branch_filter, **validated_data, serial=self.last_serial_num + 1
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
            if not transaction.draft:
                ledger_string += create_ledger_string(detail)
                update_stock(transaction.nature, {**detail, **branch_filter})

        transactions = TransactionDetail.objects.bulk_create(details)
        if not transaction.draft:
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
            "amount",
            "new",
        ]
        read_only_fields = ["transaction"]


class UpdateTransactionSerializer(ValidateTransactionSerial, serializers.ModelSerializer):

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
            "draft",
            "account_type",
            "paid_amount",
            "detail",
            "manual_invoice_serial",
            "manual_serial_type",
            "requires_action",
        ]

    def update(self, instance, validated_data):
        transaction_detail = validated_data.pop("transaction_detail")
        branch = self.context["request"].branch
        branch_filter = {"branch": branch}

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
            amount += detail["amount"]
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
                detail_instance.amount = detail["amount"]
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
        ledger_instance.draft = validated_data["draft"]
        ledger_instance.nature = validated_data["nature"]
        ledger_instance.amount = amount
        ledger_instance.person = validated_data["person"]
        if validated_data["date"]:
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
                    "draft": instance.draft,
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
            paid_instance.draft = validated_data["draft"]
            paid_instance.person = validated_data["person"]
            if validated_data["date"]:
                paid_instance.date = validated_data["date"]
            paid_instance.save()

        return super().update(instance, validated_data)


class CancelledInvoiceSerializer(ValidateTransactionSerial, serializers.ModelSerializer):
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
        branch = self.context["request"].branch
        if CancelledInvoice.objects.filter(
            branch=branch,
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
        branch = self.context["request"].branch
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
            return super().create(validated_data)
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
            "from_warehouse",
            "to_warehouse",
            "quantity",
        ]


class TransferStockSerializer(serializers.ModelSerializer):

    transfer_detail = TransferStockDetail(many=True, required=True)

    class Meta:
        model = StockTransfer
        fields = ["id", "date", "serial", "transfer_detail"]
        read_only_fields = ["id", "serial"]

    def validate(self, data):
        # if not is_array_unique(data["transfer_detail"], "stock_id"):
        #     raise serializers.ValidationError(
        #         "Transfer detail is not unique", status.HTTP_400_BAD_REQUEST
        #     )
        for row in data["transfer_detail"]:
            if row["from_warehouse"] == row["to_warehouse"]:
                raise serializers.ValidationError(
                    "You are trying to transfer to same warehouse product is in",
                    status.HTTP_400_BAD_REQUEST,
                )
        return data

    def create(self, validated_data):
        branch = self.context["request"].branch
        transfer_detail = validated_data.pop("transfer_detail")
        transfer_instance = StockTransfer.objects.create(
            **validated_data,
            serial=StockTransfer.get_next_serial(branch, "serial"),
            branch=branch,
        )
        detail_entries = []
        for detail in transfer_detail:
            data = {
                "product": detail["product"],
                "warehouse": detail["from_warehouse"],
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
        fields = ["id", "date", "serial", "transfer_detail"]
