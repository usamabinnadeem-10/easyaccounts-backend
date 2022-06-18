from authentication.choices import RoleChoices
from essentials.choices import PersonChoices

from .models import CancelledInvoice, CancelStockTransfer, StockTransfer, Transaction


class TransactionQuery:
    def get_queryset(self):
        customer_filter = {}
        if self.request.role != RoleChoices.ADMIN:
            customer_filter["person__person_type"] = PersonChoices.CUSTOMER
        return Transaction.objects.filter(
            person__branch=self.request.branch, **customer_filter
        )


class CancelledInvoiceQuery:
    def get_queryset(self):
        return CancelledInvoice.objects.filter(branch=self.request.branch)


class TransferQuery:
    def get_queryset(self):
        return StockTransfer.objects.filter(branch=self.request.branch)


class CancelStockTransferQuery:
    def get_queryset(self):
        return CancelStockTransfer.objects.filter(warehouse__branch=self.request.branch)
