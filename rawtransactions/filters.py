from django_filters import rest_framework as filters

from .models import RawTransaction


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
