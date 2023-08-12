from rest_framework.exceptions import AuthenticationFailed

from .models import UserBranchRelation


class UserBranchQuery:
    """this query returns all the branches that user is a part of"""

    def get_queryset(self):
        user_branches = UserBranchRelation.objects.select_related("branch").filter(
            user=self.request.user, is_active=True
        )
        if not user_branches:
            raise AuthenticationFailed("User does not exist")
        return user_branches


class UserQuery:
    """this query returns all the users of the branch"""

    def get_queryset(self):
        return UserBranchRelation.objects.filter(branch=self.request.branch).order_by(
            "user"
        )
