from uuid import uuid4
from rest_framework import serializers
from essentials.models import AccountType
import transactions

from .models import *
from ledgers.models import Ledger
from essentials.serializers import AccountTypeSerializer

from django.db.models import Max


class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = [
            "id",
            "transaction",
            "product",
            "rate",
            "quantity",
            "warehouse",
            "amount",
        ]
        read_only_fields = ["id", "transaction"]


def create_ledger_entries(
    transaction, transaction_details, paid, account_type, paid_amount, ledger_string
):
    amount = 0.0
    for t in transaction_details:
        amount += t["amount"]
    amount -= transaction.discount
    ledger_data = [
        Ledger(
            **{
                "detail": ledger_string,
                "amount": amount,
                "transaction": transaction,
                "nature": transaction.nature,
                "person": transaction.person,
                "date": transaction.date,
                "draft": transaction.draft,
            }
        )
    ]
    if paid:
        ledger_data.append(
            Ledger(
                **{
                    "detail": f"Paid on {account_type.name}",
                    "amount": paid_amount,
                    "transaction": transaction,
                    "nature": "C",
                    "account_type": account_type,
                    "person": transaction.person,
                    "date": transaction.date,
                    "draft": transaction.draft,
                }
            )
        )

    return ledger_data


class TransactionSerializer(serializers.ModelSerializer):

    transaction_detail = TransactionDetailSerializer(many=True)
    paid = serializers.BooleanField(default=False)
    paid_amount = serializers.FloatField(write_only=True, required=False, default=0.0)
    account_type = serializers.UUIDField(required=False, write_only=True)
    serial = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "serial",
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
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        account_type = None
        if validated_data["paid"]:
            account_type = AccountType.objects.get(
                id=validated_data.pop("account_type")
            )

        transaction_details = validated_data.pop("transaction_detail")
        paid = validated_data.pop("paid")
        paid_amount = validated_data.pop("paid_amount")

        last_serial_num = Transaction.objects.aggregate(Max("serial"))
        if last_serial_num:
            last_serial_num = last_serial_num["serial__max"]
        else:
            last_serial_num = 0
        transaction = Transaction.objects.create(
            **validated_data, serial=last_serial_num + 1
        )
        details = []
        ledger_string = ""
        for detail in transaction_details:
            ledger_string += (
                detail["product"].product_head.head_name
                + " / "
                + detail["product"].product_color.color_name
                + " @ PKR "
                + str(detail["rate"])
                + "\n"
            )
            details.append(TransactionDetail(transaction_id=transaction.id, **detail))

        TransactionDetail.objects.bulk_create(details)

        ledger_data = create_ledger_entries(
            transaction,
            transaction_details,
            paid,
            account_type,
            paid_amount,
            ledger_string,
        )
        Ledger.objects.bulk_create(ledger_data)
        validated_data["transaction_detail"] = transaction_details
        validated_data["id"] = transaction.id
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
            "quantity",
            "warehouse",
            "amount",
            "new",
        ]
        read_only_fields = ["transaction"]


class UpdateTransactionSerializer(serializers.ModelSerializer):

    transaction_detail = UpdateTransactionDetailSerializer(many=True)
    paid = serializers.BooleanField(default=False)
    paid_amount = serializers.FloatField(write_only=True, required=False, default=0.0)
    account_type = serializers.UUIDField(required=False)
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
            "paid",
            "account_type",
            "paid_amount",
        ]

    def update(self, instance, validated_data):

        transaction_detail = validated_data.pop("transaction_detail")

        # delete all the other transaction details which were not in the transaction_detail
        all_transaction_details = TransactionDetail.objects.filter(transaction=instance)
        ids_to_keep = []
        for detail in transaction_detail:
            if not detail["new"]:
                ids_to_keep.append(detail["id"])
        for transaction in all_transaction_details:
            if not transaction.id in ids_to_keep:
                to_delete = TransactionDetail.objects.get(id=transaction.id)
                to_delete.delete()

        ledger_string = ""
        # for all the details, if it is new then create it otherwise edit the previous
        amount = 0.0
        for detail in transaction_detail:
            amount += detail["amount"]
            if detail["new"]:
                detail.pop("new")
                TransactionDetail.objects.create(transaction=instance, **detail)
            else:
                detail_instance = TransactionDetail.objects.get(id=detail["id"])
                detail_instance.product = detail["product"]
                detail_instance.rate = detail["rate"]
                detail_instance.quantity = detail["quantity"]
                detail_instance.warehouse = detail["warehouse"]
                detail_instance.amount = detail["amount"]
                detail_instance.save()
            ledger_string += (
                detail["product"].product_head.head_name
                + " / "
                + detail["product"].product_color.color_name
                + " @ PKR "
                + str(detail["rate"])
                + "\n"
            )
        amount -= validated_data["discount"]
        ledger_instance = Ledger.objects.get(
            transaction=instance, account_type__isnull=True
        )
        ledger_instance.detail = ledger_string
        ledger_instance.draft = validated_data["draft"]
        ledger_instance.nature = validated_data["nature"]
        ledger_instance.amount = amount
        ledger_instance.person = validated_data["person"]
        if validated_data["date"]:
            ledger_instance.date = validated_data["date"]
        ledger_instance.save()

        if validated_data["paid"]:
            account_type = AccountType.objects.get(
                id=validated_data.pop("account_type")
            )

        validated_data.pop("paid")
        paid_amount = validated_data.pop("paid_amount")

        # if the transaction was unpaid before and is now paid then create a new ledger entry
        if validated_data["type"] != instance.type and validated_data["type"] == "paid":
            account_type = AccountType.objects.get()
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

        return super().update(instance, validated_data)
