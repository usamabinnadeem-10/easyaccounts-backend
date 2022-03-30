from django.contrib import admin

from .models import (
    Formula,
    RawLotDetail,
    RawProduct,
    RawProductOpeningStock,
    RawReturn,
    RawReturnLot,
    RawReturnLotDetail,
    RawTransaction,
    RawTransactionLot,
)


class RawTransactionLotAdmin(admin.ModelAdmin):
    list_display = ["id", "lot_number", "issued"]


class RawLotDetailAdmin(admin.ModelAdmin):
    list_display = ["lot_number"]


# Register your models here.
admin.site.register(Formula)
admin.site.register(RawProduct)
admin.site.register(RawProductOpeningStock)
admin.site.register(RawTransaction)
admin.site.register(RawTransactionLot, RawTransactionLotAdmin)
admin.site.register(RawLotDetail, RawLotDetailAdmin)
admin.site.register(RawReturn)
admin.site.register(RawReturnLot)
admin.site.register(RawReturnLotDetail)
