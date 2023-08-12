import authentication.constants as PERMISSIONS
from authentication.choices import RoleChoices
from core.utils import check_permission
from essentials.choices import PersonChoices

from .models import StockTransfer, Transaction


class TransactionQuery:
    def get_queryset(self):
        customer_filter = {}
        if not check_permission(self.request, PERMISSIONS.CAN_VIEW_FULL_TRANSACTIONS):
            customer_filter["person__person_type"] = PersonChoices.CUSTOMER
        return Transaction.objects.filter(
            person__branch=self.request.branch, **customer_filter
        )


class TransferQuery:
    def get_queryset(self):
        return StockTransfer.objects.filter(
            from_warehouse__branch=self.request.branch
        ).order_by("date")
