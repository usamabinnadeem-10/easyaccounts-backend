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
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):

        transaction_details = validated_data.pop("transaction_detail")
        paid = validated_data.pop("paid")

        last_serial_num = (
            Transaction.objects.aggregate(Max("serial"))["serial__max"] or 0
        )
        transaction = Transaction.objects.create(
            **validated_data, serial=last_serial_num + 1
        )
        details = []
        ledger_string = ""
        for detail in transaction_details:
            ledger_string += create_ledger_string(detail)
            details.append(TransactionDetail(transaction_id=transaction.id, **detail))
            update_stock(transaction.nature, detail)

        transactions = TransactionDetail.objects.bulk_create(details)

        ledger_data = create_ledger_entries(
            transaction,
            transaction_details,
            paid,
            ledger_string + f'{validated_data["detail"]}\n',
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
        ]

    def update(self, instance, validated_data):
        transaction_detail = validated_data.pop("transaction_detail")

        # delete all the other transaction details which were not in the transaction_detail
        all_transaction_details = TransactionDetail.objects.filter(
            transaction=instance
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
                to_delete = TransactionDetail.objects.get(id=transaction["id"])
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
                TransactionDetail.objects.create(transaction=instance, **detail)
            else:
                detail_instance = TransactionDetail.objects.get(id=detail["id"])
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
            transaction=instance, account_type__isnull=True
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
                }
            )

        # if transaction was paid and is now unpaid then delete the old ledger entry
        if validated_data["type"] != "paid" and instance.type == "paid":
            paid_instance = Ledger.objects.get(
                transaction=instance, account_type__isnull=False
            )
            paid_instance.delete()

        # if both types are paid then update the Ledger entry
        if validated_data["type"] == instance.type and instance.type == "paid":
            paid_instance = Ledger.objects.get(
                transaction=instance, account_type__isnull=False
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
