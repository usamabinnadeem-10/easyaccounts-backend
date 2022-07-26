from django.contrib import admin

from .models import ExpenseAccount, ExpenseDetail

admin.site.register(ExpenseAccount)
admin.site.register(ExpenseDetail)


class ExpenseAccountAdmin(admin.ModelAdmin):

    list_display = ["name", "type"]
    list_filter = ["name", "type"]


class ExpenseDetailAdmin(admin.ModelAdmin):

    list_display = ["date", "serial", "amount", "account_type"]
    list_filter = ["date", "amount"]


admin.site.register(ExpenseAccount, ExpenseAccountAdmin)
admin.site.register(ExpenseDetail, ExpenseDetailAdmin)
