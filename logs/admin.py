from django.contrib import admin

from .models import Log

# Register your models here.


class LogAdmin(admin.ModelAdmin):
    list_display = ["time_stamp", "type", "category", "user", "branch"]
    list_filter = ["branch__name"]


admin.site.register(Log, LogAdmin)
