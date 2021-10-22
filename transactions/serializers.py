from uuid import uuid4
from rest_framework import serializers
from essentials.models import AccountType

from ledgers.serializers import LedgerSerializer

from .models import *
from essentials.serializers import AccountTypeSerializer
from ledgers.models import Ledger


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


class TransactionSerializer(serializers.ModelSerializer):

    transaction_detail = TransactionDetailSerializer(many=True)
    paid = serializers.BooleanField(default=False)
    paid_amount = serializers.FloatField(write_only=True, required=False, default=0.0)
    account_type = serializers.UUIDField(required=False, write_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "date",
            "transaction_detail",
            "nature",
            "discount",
            "person",
            "draft",
            "paid",
            "account_type",
            "paid_amount",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        if validated_data["paid"]:
            account_type = AccountType.objects.get(
                id=validated_data.pop("account_type")
            )

        transaction_details = validated_data.pop("transaction_detail")
        paid = validated_data.pop("paid")
        paid_amount = validated_data.pop("paid_amount")

        transaction = Transaction.objects.create(**validated_data)
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
                    }
                )
            )
        Ledger.objects.bulk_create(ledger_data)
        validated_data["transaction_detail"] = transaction_details
        return validated_data
