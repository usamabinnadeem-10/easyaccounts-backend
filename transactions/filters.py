from django_filters import rest_framework as filters

from .models import Transaction


class TransactionsFilter(filters.FilterSet):

    transaction_detail__product__category = filters.CharFilter(
        field_name="transaction_detail__product__category", distinct=True
    )

    class Meta:
        model = Transaction
        fields = {
            "date": ["gte", "lte"],
            "account_type": ["exact"],
            "detail": ["icontains"],
            "person": ["exact"],
            "serial": ["exact", "gte", "lte"],
            "manual_serial": ["exact", "gte", "lte"],
            "wasooli_number": ["exact", "gte", "lte"],
            "serial_type": ["exact"],
            "discount": ["gte", "lte"],
            "type": ["exact"],
            "requires_action": ["exact"],
            "transaction_detail__product": ["exact"],
            # "transaction_detail__product__category": ["exact"],
            "transaction_detail__warehouse": ["exact"],
        }
