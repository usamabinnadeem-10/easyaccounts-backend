from rest_framework import serializers

from .models import ExpenseAccount, ExpenseDetail


class ExpenseAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseAccount
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance


class ExpenseDetailSerializer(serializers.ModelSerializer):

    expense_name = serializers.CharField(source="expense.name", read_only=True)
    account_type_name = serializers.CharField(source="account_type.name", read_only=True)

    class Meta:
        model = ExpenseDetail
        fields = [
            "id",
            "expense",
            "detail",
            "amount",
            "account_type",
            "date",
            "expense_name",
            "account_type_name",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        return instance
