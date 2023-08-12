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
        request.permissions = user_branch.permissions
        return True


class ValidatePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return True
        target_permissions = view.permissions if hasattr(view, "permissions") else None
        user_permissions = request.permissions

        if target_permissions:
            if type(target_permissions) == list:
                permitted = True
                for permission in target_permissions:
                    if not (permission in user_permissions):
                        permitted = False
                        break
                return permitted

            elif type(target_permissions) == dict:
                or_permissions = target_permissions.get("or", [])
                and_permissions = target_permissions.get("and", [])

                or_allowed = True if len(or_permissions) == 0 else False
                and_allowed = True

                for or_perm in or_permissions:
                    if or_perm in user_permissions:
                        or_allowed = True
                        break

                for and_perm in and_permissions:
                    if not (and_perm in user_permissions):
                        and_allowed = False
                        break

                return or_allowed and and_allowed
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


class IsHeadAccountant(permissions.BasePermission):
    """Permission class to check whether user is a head accountant"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.HEAD_ACCOUNTANT


class IsAdminReadOnly(permissions.BasePermission):
    """Permission class to check whether user is a read only admin"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.ADMIN_VIEWER


class IsStockist(permissions.BasePermission):
    """Permission class to check whether user is a stockist"""

    def has_permission(self, request, view):
        return request.role == RoleChoices.STOCKIST
