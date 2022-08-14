from django.contrib import admin

from .models import (
    Formula,
    RawProduct,
    RawPurchase,
    RawPurchaseLot,
    RawPurchaseLotDetail,
    RawSaleAndReturn,
    RawSaleAndReturnLotDetail,
    RawSaleAndReturnWithPurchaseLotRelation,
    RawStockTransfer,
    RawStockTransferAndLotRelation,
    RawStockTransferLotDetail,
)


class RawPurchaseAdmin(admin.ModelAdmin):
    list_display = ["person", "serial"]


class RawProductAdmin(admin.ModelAdmin):
    list_display = ["person", "name", "type"]


class RawPurchaseLotAdmin(admin.ModelAdmin):
    list_display = ["id", "raw_purchase", "lot_number", "issued"]


class RawPurchaseLotDetailAdmin(admin.ModelAdmin):
    list_display = ["purchase_lot_number"]


# Register your models here.
admin.site.register(Formula)
admin.site.register(RawProduct, RawProductAdmin)
admin.site.register(RawPurchase, RawPurchaseAdmin)
admin.site.register(RawPurchaseLot, RawPurchaseLotAdmin)
admin.site.register(RawPurchaseLotDetail, RawPurchaseLotDetailAdmin)
admin.site.register(RawSaleAndReturn)
admin.site.register(RawSaleAndReturnWithPurchaseLotRelation)
admin.site.register(RawSaleAndReturnLotDetail)
admin.site.register(RawStockTransfer)
admin.site.register(RawStockTransferAndLotRelation)
admin.site.register(RawStockTransferLotDetail)
