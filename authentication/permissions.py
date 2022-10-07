from rest_framework import permissions

from .choices import RoleChoices
from .models import UserBranchRelation


class IsLoggedIn(permissions.BasePermission):
    """This permission class is used to check whether the authenticated user is logged in a branch or not."""

    def has_permission(self, request, view):
        try:
            user_branch = UserBranchRelation.objects.get(
                user=request.user, is_logged_in=True, is_active=True
            )
        except UserBranchRelation.DoesNotExist:
            return False
        request.branch = user_branch.branch
        request.role = user_branch.role
        return True


class IsBranchMember(permissions.BasePermission):
    """This permission class is used to check whether user is a part of at least one branch"""

    def has_permission(self, request, view):
        return UserBranchRelation.objects.filter(user=request.user).exists()


class IsAdmin(permissions.BasePermission):
    """Permission class to check whether user is an admin"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.ADMIN


class IsPurchaser(permissions.BasePermission):
    """Permission class to check whether user is a purchaser"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.PURCHASER


class IsSaleman(permissions.BasePermission):
    """Permission class to check whether user is a saleman"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.SALEMAN


class IsAccountant(permissions.BasePermission):
    """Permission class to check whether user is a saleman"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.ACCOUNTANT


class IsAdminReadOnly(permissions.BasePermission):
    """Permission class to check whether user is a read only admin"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.ADMIN_VIEWER


class IsStockist(permissions.BasePermission):
    """Permission class to check whether user is a stockist"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.STOCKIST
