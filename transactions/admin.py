from django.contrib import admin

from .models import (  # CancelledInvoice,; CancelStockTransfer,
    StockTransfer,
    StockTransferDetail,
    Transaction,
    TransactionDetail,
)


class TransactionAdmin(admin.ModelAdmin):

    list_display = ["id", "date"]


class CancelStockTransferAdmin(admin.ModelAdmin):

    list_display = ["warehouse", "manual_invoice_serial"]


# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionDetail)
# admin.site.register(CancelledInvoice)
admin.site.register(StockTransfer)
admin.site.register(StockTransferDetail)
# admin.site.register(CancelStockTransfer, CancelStockTransferAdmin)
