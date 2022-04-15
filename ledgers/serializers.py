from rest_framework import serializers

from .models import *


class LedgerSerializer(serializers.ModelSerializer):

    transaction_serial = serializers.CharField(
        source="transaction.serial", read_only=True
    )
    manual_invoice_serial = serializers.IntegerField(
        source="transaction.manual_invoice_serial", read_only=True
    )
    manual_serial_type = serializers.CharField(
        source="transaction.manual_serial_type", read_only=True
    )

    class Meta:
        model = Ledger
        fields = [
            "id",
            "person",
            "date",
            "detail",
            "amount",
            "nature",
            "account_type",
            "transaction",
            "draft",
            "transaction_serial",
            "manual_invoice_serial",
            "manual_serial_type",
            "external_cheque",
            "personal_cheque",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "account_type": {"required": False},
            "transaction": {"required": False},
        }

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        return instance
