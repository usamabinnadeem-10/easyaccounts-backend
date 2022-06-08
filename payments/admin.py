from django.contrib import admin

from .models import Payment, PaymentImage

# Register your models here.
admin.site.register(Payment)
admin.site.register(PaymentImage)
