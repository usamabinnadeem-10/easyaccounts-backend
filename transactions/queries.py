from .models import CancelledInvoice, CancelStockTransfer, StockTransfer, Transaction


class TransactionQuery:
    def get_queryset(self):
        return Transaction.objects.filter(branch=self.request.branch)


class CancelledInvoiceQuery:
    def get_queryset(self):
        return CancelledInvoice.objects.filter(branch=self.request.branch)


class TransferQuery:
    def get_queryset(self):
        return StockTransfer.objects.filter(branch=self.request.branch)


class CancelStockTransferQuery:
    def get_queryset(self):
        return CancelStockTransfer.objects.filter(branch=self.request.branch)
