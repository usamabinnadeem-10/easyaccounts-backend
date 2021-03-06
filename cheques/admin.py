from django.contrib import admin

from .models import *


class ExternalChequeAdmin(admin.ModelAdmin):
    list_display = ["id", "serial"]


class ExternalChequeHistoryAdmin(admin.ModelAdmin):
    list_display = ["parent_cheque", "cheque", "amount", "return_cheque"]


class ExternalChequeTransferAdmin(admin.ModelAdmin):
    list_display = ["cheque", "person"]


class PersonalChequeAdmin(admin.ModelAdmin):
    list_display = ["id", "serial", "amount"]


admin.site.register(ExternalCheque, ExternalChequeAdmin)
admin.site.register(ExternalChequeHistory, ExternalChequeHistoryAdmin)
admin.site.register(ExternalChequeTransfer, ExternalChequeTransferAdmin)
admin.site.register(PersonalCheque, PersonalChequeAdmin)
