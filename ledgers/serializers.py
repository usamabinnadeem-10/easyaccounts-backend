from rest_framework import serializers

from .models import Ledger
class LedgerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ledger
        fields = ['id', 'date', 'detail', 'amount', 'person', 'transaction', 'account_type', 'nature']
