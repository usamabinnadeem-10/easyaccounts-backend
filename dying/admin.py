from django.contrib import admin

from .models import DyingIssue, DyingIssueDetail, DyingUnit


class DyingUnitAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class DyingIssueAdmin(admin.ModelAdmin):
    list_display = ["id", "dying_unit", "lot_number", "dying_lot_number"]


admin.site.register(DyingUnit, DyingUnitAdmin)
admin.site.register(DyingIssue, DyingIssueAdmin)
admin.site.register(DyingIssueDetail)
