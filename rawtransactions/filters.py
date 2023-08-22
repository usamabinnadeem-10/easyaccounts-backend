from django_filters import rest_framework as filters

from .models import RawDebit, RawTransaction, RawTransfer


class RawTransactionsFilter(filters.FilterSet):
    class Meta:
        model = RawTransaction
        fields = {
            "id": ["exact"],
            "date": ["gte", "lte"],
            "person": ["exact"],
            "serial": ["exact", "gte", "lte"],
            "manual_serial": ["exact", "gte", "lte"],
            "lots__raw_product": ["exact"],
            "lots__lot_number": ["exact", "gte", "lte"],
            "lots__issued": ["exact"],
        }


class RawDebitTransactionsFilter(filters.FilterSet):
    class Meta:
        model = RawDebit
        fields = {
            "id": ["exact"],
            "date": ["gte", "lte"],
            "person": ["exact"],
            "debit_type": ["exact"],
            "serial": ["exact", "gte", "lte"],
            "manual_serial": ["exact", "gte", "lte"],
            "lots__lot_number": ["exact", "gte", "lte"],
        }


class RawTransferTransactionsFilter(filters.FilterSet):
    class Meta:
        model = RawTransfer
        fields = {
            "id": ["exact"],
            "date": ["gte", "lte"],
            "serial": ["exact", "gte", "lte"],
            "manual_serial": ["exact", "gte", "lte"],
            "lots__lot_number": ["exact", "gte", "lte"],
        }