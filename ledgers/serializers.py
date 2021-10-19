from rest_framework import serializers

from .models import Ledger
from essentials.models import AccountType


class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = [
            "id",
            "date",
            "detail",
            "amount",
            "person",
            "transaction",
            "account_type",
            "nature",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        data = self.data
        account_type = data["account_type"]
        if account_type:
            account = AccountType.objects.get(id=account_type)
            amount = data["amount"]
            if data["nature"] == "C":
                account.balance = account.balance + amount
            else:
                account.balance = account.balance - amount
            account.save()
        return super().create(validated_data)
