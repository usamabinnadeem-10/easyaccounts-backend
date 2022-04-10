from .models import CancelledInvoice, StockTransfer, Transaction


class TransactionQuery:
    def get_queryset(self):
        return Transaction.objects.filter(branch=self.request.branch)


class CancelledInvoiceQuery:
    def get_queryset(self):
        return CancelledInvoice.objects.filter(branch=self.request.branch)


class TransferQuery:
    def get_queryset(self):
        return StockTransfer.objects.filter(branch=self.request.branch)
