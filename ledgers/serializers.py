from rest_framework import serializers

from .models import *


class LedgerSerializer(serializers.ModelSerializer):

    person_name = serializers.CharField(source="person.name", read_only=True)
    account_type_name = serializers.CharField(
        source="account_type.name", read_only=True
    )
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
            "person_name",
            "account_type_name",
            "transaction_serial",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "account_type": {"required": False},
            "transaction": {"required": False},
        }
