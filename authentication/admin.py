from django.contrib import admin

from .models import *


class BranchAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class UserBranchRelationAdmin(admin.ModelAdmin):
    list_display = ["user", "branch", "role", "is_logged_in"]


# Register your models here.
admin.site.register(Branch, BranchAdmin)
admin.site.register(UserBranchRelation, UserBranchRelationAdmin)
