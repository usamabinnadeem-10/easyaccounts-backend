from rest_framework import serializers

from .models import *


class LedgerSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "account_type": {"required": False},
            "transaction": {"required": False},
        }
