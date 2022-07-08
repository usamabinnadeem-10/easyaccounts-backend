from django.contrib import admin

from .models import *


class PersonAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "person_type"]
    list_filter = ["branch__name", "name", "person_type"]
    search_fields = ["name", "phone_number"]


class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_filter = ["category__branch__name", "category"]
    search_fields = ["name"]


class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_filter = ["branch__name", "name"]
    search_fields = ["name"]


class StockAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "warehouse"]
    list_filter = [
        "warehouse__branch__name",
        "product__category__name",
        "warehouse",
    ]
    search_fields = ["product"]


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
admin.site.register(OpeningSaleData)
