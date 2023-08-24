from django.contrib import admin

from .models import DyingIssue, DyingIssueDetail, DyingIssueLot, DyingUnit


class DyingUnitAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class DyingIssueAdmin(admin.ModelAdmin):
    list_display = ["id", "dying_unit", "manual_serial"]


admin.site.register(DyingUnit, DyingUnitAdmin)
admin.site.register(DyingIssue, DyingIssueAdmin)
admin.site.register(DyingIssueDetail)
admin.site.register(DyingIssueLot)
