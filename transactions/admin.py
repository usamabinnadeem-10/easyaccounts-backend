from django.contrib import admin

from .models import *


class TransactionAdmin(admin.ModelAdmin):

    list_display = ["id", "date"]


# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionDetail)
admin.site.register(CancelledInvoice)
