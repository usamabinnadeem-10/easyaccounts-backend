from core.utils import get_cheque_account
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import serializers, status

from .models import ExpenseAccount, ExpenseDetail


class ValidateAccountType:
    def validate(self, data):
        if (
            data["account_type"]
            == get_cheque_account(self.context["request"].branch).account
        ):
            raise serializers.ValidationError(
                "Please use another account type for transaction",
                status.HTTP_400_BAD_REQUEST,
            )
        return data


class ExpenseAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseAccount
        fields = ["id", "name", "type"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance


class ExpenseDetailSerializer(ValidateAccountType, serializers.ModelSerializer):

    request = None

    class Meta:
        model = ExpenseDetail
        fields = [
            "id",
            "serial",
            "expense",
            "detail",
            "amount",
            "account_type",
            "date",
        ]
        read_only_fields = ["id", "serial"]

    def create(self, validated_data):
        self.request = self.context["request"]
        validated_data["user"] = self.request.user
        validated_data["serial"] = ExpenseDetail.get_next_serial(
            "serial", expense__branch=self.request.branch
        )
        instance = super().create(validated_data)
        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.EXPENSE,
            f"'{instance.account_type.name}' for {instance.amount}",
            self.request,
        )
        return instance
