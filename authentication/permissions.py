from rest_framework import permissions

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
