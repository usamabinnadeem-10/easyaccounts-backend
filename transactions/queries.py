import authentication.constants as PERMISSIONS
from core.utils import check_permission
from essentials.choices import PersonChoices

from .models import StockTransfer, Transaction


class TransactionQuery:
    def get_queryset(self):
        person_filter = []
        if not check_permission(self.request, PERMISSIONS.CAN_VIEW_CUSTOMER_TRANSACTIONS):
            person_filter.append("C")
        if not check_permission(self.request, PERMISSIONS.CAN_VIEW_SUPPLIER_TRANSACTIONS):
            person_filter.append("S")
        return Transaction.objects.filter(person__branch=self.request.branch).exclude(
            person__person_type__in=person_filter
        )


class TransferQuery:
    def get_queryset(self):
        return StockTransfer.objects.filter(
            from_warehouse__branch=self.request.branch
        ).order_by("date")
