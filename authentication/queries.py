from rest_framework.exceptions import AuthenticationFailed

from .models import UserBranchRelation


class UserBranchQuery:
    """this query returns all the branches that user is a part of"""

    def get_queryset(self):
        user_branches = UserBranchRelation.objects.select_related("branch").filter(
            user=self.request.user
        )
        if not user_branches:
            raise AuthenticationFailed("User does not exist")
        return user_branches
