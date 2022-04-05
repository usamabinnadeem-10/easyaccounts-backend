from django.contrib import admin

from .models import *


class PersonAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "person_type"]


class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_filter = ["category"]


class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class StockAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "warehouse", "stock_quantity"]


class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(LinkedAccount)
admin.site.register(Area)
admin.site.register(ProductCategory, ProductCategoryAdmin)
