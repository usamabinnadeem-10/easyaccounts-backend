from uuid import uuid4
from rest_framework import serializers

from .models import Transaction, TransactionDetail
from essentials.models import AccountType, Product
from ledgers.models import Ledger


class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = ["id", "transaction_id", "product", "rate", "quantity"]
        read_only_fields = ["transaction_id"]


class TransactionSerializer(serializers.ModelSerializer):

    transactions = TransactionDetailSerializer(many=True)
    account_type = serializers.UUIDField()
    amount = serializers.FloatField()
    paid = serializers.BooleanField()
    detail = serializers.CharField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "date",
            "transactions",
            "nature",
            "discount",
            "warehouse",
            "person",
            "account_type",
            "amount",
            "paid",
            "detail",
            "draft",
        ]

    def create(self, validated_data):
        account_type = validated_data.pop("account_type")
        amount = validated_data.pop("amount")
        paid = validated_data.pop("paid")
        detail = validated_data.pop("detail")
        transaction_details = validated_data.pop("transactions")

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

        """UPDATE BALANCE ON THE ACCOUNT TYPE"""
        if account_type:
            account = AccountType.objects.get(id=account_type)
            account.balance = account.balance + amount
            account.save()

        nature = "C" if paid else "D"
        Ledger.objects.create(
            detail=detail,
            amount=amount,
            person=validated_data["person"],
            transaction=transaction,
            account_type=account,
            nature=nature,
        )

        return {}
