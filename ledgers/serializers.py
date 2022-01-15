from rest_framework import serializers

from .models import *


class LedgerSerializer(serializers.ModelSerializer):

    transaction_serial = serializers.CharField(
        source="transaction.serial", read_only=True
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
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "account_type": {"required": False},
            "transaction": {"required": False},
        }
