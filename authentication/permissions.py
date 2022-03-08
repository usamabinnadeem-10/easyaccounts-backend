from rest_framework import permissions

from .models import UserBranchRelation


class IsLoggedIn(permissions.BasePermission):
    """This permission class is used to check whether the authenticated user is logged in a tenant or not."""

    def has_permission(self, request, view):
        """Overriding this method to implement how permissions are going to be determined."""
        try:
            user_branch = UserBranchRelation.objects.get(
                user=request.user, is_logged_in=True
            )
        except UserBranchRelation.DoesNotExist:
            return False
        request.branch = user_branch.branch
        request.role = user_branch.role
        return True
