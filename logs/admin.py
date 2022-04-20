from django.contrib import admin

from .models import Log

# Register your models here.


class LogAdmin(admin.ModelAdmin):
    list_display = ["time_stamp", "type", "category", "user", "branch"]


admin.site.register(Log, LogAdmin)
