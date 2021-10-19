from uuid import uuid4
from rest_framework import serializers

from ledgers.serializers import LedgerSerializer

from .models import Transaction, TransactionDetail
from essentials.models import AccountType, Product
from ledgers.models import Ledger


class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = ["id", "transaction_id", "product", "rate", "quantity"]
        read_only_fields = ["transaction_id"]


class TransactionSerializer(serializers.ModelSerializer):

    transaction_detail = TransactionDetailSerializer(many=True)
    ledger_data = LedgerSerializer(many=True, write_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "date",
            "transaction_detail",
            "nature",
            "discount",
            "warehouse",
            "person",
            "ledger_data",
            "draft",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        transaction_details = validated_data.pop("transaction_detail")
        ledger_data = validated_data.pop("ledger_data")

        """CREATE TRANSACTION AND TRANSACTION DETAILS. UPDATE PRODUCT QUANTITIES"""
        transaction = Transaction.objects.create(**validated_data)
        for detail in transaction_details:
            transaction_detail = TransactionDetail.objects.create(
                transaction_id=transaction, **detail
            )
            product = Product.objects.get(id=transaction_detail.product.id)
            if validated_data["nature"] == "D":
                product.current_quantity = product.current_quantity - detail["quantity"]
            else:
                product.current_quantity = product.current_quantity + detail["quantity"]
            product.save()

        validated_data["transaction_detail"] = transaction_details
        ledger_data[0]["transaction"] = transaction
        for ledger in ledger_data:
            Ledger.objects.create(**ledger)

        return validated_data
