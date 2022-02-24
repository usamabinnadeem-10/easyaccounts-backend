from rest_framework.permissions import BasePermission

from .models import UserBranchRelation
from .choices import RoleChoices


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = UserBranchRelation.objects.get(request["user"])
        return user.role == RoleChoices.ADMIN
