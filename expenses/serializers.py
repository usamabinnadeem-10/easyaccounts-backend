from rest_framework import serializers
from .models import ExpenseAccount, ExpenseDetail

from essentials.models import AccountType


class ExpenseAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseAccount
        fields = ["id", "name"]
        read_only_fields = ["id"]


class ExpenseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseDetail
        fields = ["id", "expense", "detail", "amount", "account_type", "date"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        account_type = validated_data["account_type"]
        if account_type:
            account = AccountType.objects.get(id=account_type)
            account.balance = account.balance - validated_data["amount"]
            account.save()
        return super().create(validated_data)
