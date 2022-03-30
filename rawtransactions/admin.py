from django.contrib import admin

from .models import (
    Formula,
    RawDebit,
    RawDebitLot,
    RawDebitLotDetail,
    RawLotDetail,
    RawProduct,
    RawProductOpeningStock,
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
admin.site.register(RawDebit)
admin.site.register(RawDebitLot)
admin.site.register(RawDebitLotDetail)
