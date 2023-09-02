from django.contrib import admin

from .models import StockTransfer, StockTransferDetail, Transaction, TransactionDetail


class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "date", "serial_type", "serial"]
    list_filter = ["person__branch__name"]


class StockAdmin(admin.ModelAdmin):
    list_display = ["id", "serial", "from_warehouse", "manual_serial"]
    list_filter = ["from_warehouse__branch__name"]


# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionDetail)
admin.site.register(StockTransfer, StockAdmin)
admin.site.register(StockTransferDetail)
