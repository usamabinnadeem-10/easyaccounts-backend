from django.contrib import admin

from .models import DyingIssue, DyingIssueDetail, DyingUnit

admin.site.register(DyingUnit)
admin.site.register(DyingIssue)
admin.site.register(DyingIssueDetail)
