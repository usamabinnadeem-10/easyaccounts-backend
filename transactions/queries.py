from .models import CancelledInvoice, Transaction, TransactionDetail, TransferEntry


class TransactionQuery:
    def get_queryset(self):
        return Transaction.objects.filter(branch=self.request.branch)


class CancelledInvoiceQuery:
    def get_queryset(self):
        return CancelledInvoice.objects.filter(branch=self.request.branch)
