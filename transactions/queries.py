import authentication.constants as PERMISSIONS
from core.utils import check_permission
from essentials.choices import PersonChoices
from transactions.choices import TransactionSerialTypes

from .models import StockTransfer, Transaction


class TransactionQuery:
    def get_queryset(self):
        transaction_type_filter = []
        if not check_permission(self.request, PERMISSIONS.CAN_VIEW_CUSTOMER_TRANSACTIONS):
            transaction_type_filter.append(TransactionSerialTypes.INV)
            transaction_type_filter.append(TransactionSerialTypes.MWC)
        if not check_permission(self.request, PERMISSIONS.CAN_VIEW_SUPPLIER_TRANSACTIONS):
            transaction_type_filter.append(TransactionSerialTypes.SUP)
            transaction_type_filter.append(TransactionSerialTypes.MWS)
        return Transaction.objects.filter(person__branch=self.request.branch).exclude(
            serial_type__in=transaction_type_filter
        )


class TransferQuery:
    def get_queryset(self):
        return StockTransfer.objects.filter(
            from_warehouse__branch=self.request.branch
        ).order_by("date")
