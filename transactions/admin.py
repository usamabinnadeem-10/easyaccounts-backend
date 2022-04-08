from django.contrib import admin

from .models import CancelledInvoice, StockTransfer, StockTransferDetail, Transaction


class TransactionAdmin(admin.ModelAdmin):

    list_display = ["id", "date"]


# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(CancelledInvoice)
admin.site.register(StockTransfer)
admin.site.register(StockTransferDetail)
