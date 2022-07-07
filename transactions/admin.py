from django.contrib import admin

from .models import StockTransfer, StockTransferDetail, Transaction, TransactionDetail


class TransactionAdmin(admin.ModelAdmin):

    list_display = ["id", "date", "serial_type", "serial"]
    list_filter = ["person__branch__name"]


# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionDetail)
admin.site.register(StockTransfer)
admin.site.register(StockTransferDetail)
