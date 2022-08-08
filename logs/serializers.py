from datetime import date

from ledgers.models import Ledger
from rest_framework import serializers, status
from transactions.models import TransactionDetail

from .models import Log


class LogSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField()

    class Meta:
        model = Log
        fields = ["id", "time_stamp", "type", "category", "detail", "username"]

    def get_username(self, obj):
        return str(obj.user)
