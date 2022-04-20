from datetime import date

from ledgers.models import Ledger
from rest_framework import serializers, status
from transactions.models import TransactionDetail

from .models import Log


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ["time_stamp", "type", "category", "detail", "user"]
