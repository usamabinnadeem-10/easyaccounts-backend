from django_filters import rest_framework as filters

from .models import RawDebit, RawTransaction


class RawTransactionsFilter(filters.FilterSet):
    class Meta:
        model = RawTransaction
        fields = {
            "date": ["gte", "lte"],
            "person": ["exact"],
            "serial": ["exact", "gte", "lte"],
            "rawtransactionlot__raw_product": ["exact"],
            "rawtransactionlot__lot_number": ["exact", "gte", "lte"],
            "rawtransactionlot__issued": ["exact"],
        }


class RawDebitTransactionsFilter(filters.FilterSet):
    class Meta:
        model = RawDebit
        fields = {
            "date": ["gte", "lte"],
            "person": ["exact"],
            "debit_type": ["exact"],
            "serial": ["exact", "gte", "lte"],
            "rawdebitlot__lot_number__lot_number": ["exact", "gte", "lte"],
        }
