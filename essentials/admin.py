from django.contrib import admin

from .models import *


class PersonAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "person_type"]


class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "balance"]


admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(Product)
admin.site.register(ProductColor)
admin.site.register(ProductHead)
admin.site.register(Warehouse)
admin.site.register(Person, PersonAdmin)
