from rest_framework import serializers
from .models import ExpenseAccount, ExpenseDetail


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
