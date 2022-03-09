from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable
from essentials.models import Stock
from .models import *
from ledgers.models import Ledger

from django.db.models import Max
from django.shortcuts import get_object_or_404

from .utils import *


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


class TransactionSerializer(serializers.ModelSerializer):

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
        ]
        read_only_fields = ["id"]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Transaction.objects.all(),
                fields=("manual_invoice_serial", "manual_serial_type"),
                message="Invoice with that book number exists.",
            )
        ]

    def create(self, validated_data):
        transaction_details = validated_data.pop("transaction_detail")
        paid = validated_data.pop("paid")

        branch_filter = {"branch": self.context["request"].branch}
        last_serial_num = (
            Transaction.objects.filter(**branch_filter).aggregate(Max("serial"))[
                "serial__max"
            ]
            or 0
        )
        book_serial = validated_data["manual_invoice_serial"]
        max_from_cancelled = (
            CancelledInvoice.objects.filter(
                **branch_filter, manual_serial_type=validated_data["manual_serial_type"]
            ).aggregate(Max("manual_invoice_serial"))["manual_invoice_serial__max"]
            or 0
        )
        max_from_transactions = (
            Transaction.objects.filter(
                **branch_filter, manual_serial_type=validated_data["manual_serial_type"]
            ).aggregate(Max("manual_invoice_serial"))["manual_invoice_serial__max"]
            or 0
        )
        max_final = (
            max_from_cancelled
            if max_from_cancelled > max_from_transactions
            else max_from_transactions
        )

        if max_final - validated_data["manual_invoice_serial"] > 1:
            raise NotAcceptable(f"serial number {max_final} is missing")

        cancelled = None
        try:
            cancelled = CancelledInvoice.objects.get(
                **branch_filter,
                manual_invoice_serial=validated_data["manual_invoice_serial"],
                manual_serial_type=validated_data["manual_serial_type"],
            )
        except Exception:
            pass

        if cancelled:
            raise NotAcceptable(
                f"invoice with {cancelled.manual_serial_type}-{cancelled.manual_invoice_serial} exists"
            )

        transaction = Transaction.objects.create(
            **branch_filter, **validated_data, serial=last_serial_num + 1
        )
        details = []
        ledger_string = ""
        for detail in transaction_details:
            details.append(
                TransactionDetail(
                    transaction_id=transaction.id, **detail, **branch_filter
                )
            )
            if not transaction.draft:
                ledger_string += create_ledger_string(detail)
                update_stock(transaction.nature, detail)

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


class UpdateTransactionSerializer(serializers.ModelSerializer):

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
        ]

    def update(self, instance, validated_data):
        transaction_detail = validated_data.pop("transaction_detail")
        branch_filter = {"branch": self.context["request"].branch}
        # delete all the other transaction details which were not in the transaction_detail
        all_transaction_details = TransactionDetail.objects.filter(
            **branch_filter, transaction=instance
        ).values("id", "product", "warehouse", "quantity", "yards_per_piece")
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
                    "C" if instance.nature == "D" else "D", transaction, instance.nature
                )
                to_delete.delete()

        ledger_string = ""
        # for all the details, if it is new then create it otherwise edit the previous
        amount = 0.0
        for detail in transaction_detail:
            amount += detail["amount"]
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
                detail,
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

        # if the transaction was unpaid before and is now paid then create a new ledger entry
        if validated_data["type"] != instance.type and validated_data["type"] == "paid":
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
        if validated_data["type"] != "paid" and instance.type == "paid":
            paid_instance = Ledger.objects.get(
                transaction=instance, account_type__isnull=False, **branch_filter
            )
            paid_instance.delete()

        # if both types are paid then update the Ledger entry
        if validated_data["type"] == instance.type and instance.type == "paid":
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


class CancelledInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancelledInvoice
        fields = ["id", "manual_invoice_serial", "manual_serial_type", "comment"]
        read_only_fields = ["id"]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CancelledInvoice.objects.all(),
                fields=("manual_invoice_serial", "manual_serial_type"),
                message="Invoice with that book number exists.",
            )
        ]

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
