from django.contrib import admin

from .models import (
    Formula,
    RawLotDetail,
    RawProduct,
    RawProductOpeningStock,
    RawTransaction,
    RawTransactionLot,
)

# Register your models here.
admin.site.register(Formula)
admin.site.register(RawProduct)
admin.site.register(RawProductOpeningStock)
admin.site.register(RawTransaction)
admin.site.register(RawTransactionLot)
admin.site.register(RawLotDetail)
