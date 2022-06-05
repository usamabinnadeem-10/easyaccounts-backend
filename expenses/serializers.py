from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
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

    request = None

    class Meta:
        model = ExpenseDetail
        fields = [
            "id",
            "expense",
            "detail",
            "amount",
            "account_type",
            "date",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        self.request = self.context["request"]
        validated_data["user"] = self.request.user
        instance = super().create(validated_data)
        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.EXPENSE,
            f"'{instance.account_type.name}' for {instance.amount}",
            self.request,
        )
        return instance
