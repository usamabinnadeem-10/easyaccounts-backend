from django.contrib import admin

from .models import DyingUnit, DyingIssue, DyingIssueDetail

admin.site.register(DyingUnit)
admin.site.register(DyingIssue)
admin.site.register(DyingIssueDetail)
