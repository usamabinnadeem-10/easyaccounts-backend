from django.contrib import admin

from .models import (
    CancelledInvoice,
    Transaction,
    TransactionDetail,
    TransferEntry,
)


class TransactionAdmin(admin.ModelAdmin):

    list_display = ["id", "date"]


# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionDetail)
admin.site.register(CancelledInvoice)
admin.site.register(TransferEntry)
