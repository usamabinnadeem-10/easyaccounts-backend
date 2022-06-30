from django.contrib import admin

from .models import Ledger, LedgerAndDetail

# Register your models here.
admin.site.register(Ledger)
admin.site.register(LedgerAndDetail)
