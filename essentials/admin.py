from django.contrib import admin

from .models import *

admin.site.register(AccountType)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(Warehouse)
admin.site.register(Person)