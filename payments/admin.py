from django.contrib import admin

from .models import Payment, PaymentImage


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "date", "serial", "account_type"]
    list_filter = ["person__branch__name"]


# Register your models here.
admin.site.register(Payment, PaymentAdmin)
admin.site.register(PaymentImage)
