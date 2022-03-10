from rest_framework.permissions import IsAuthenticated
from .permissions import IsBranchMember


class IsAuthenticatedPermissionMixin:
    """To check if user is authenticated"""

    permission_classes = [
        IsAuthenticated,
    ]


class HasBranchPermissionMixin:
    """To check if the user is authenticated and is a member of at least one branch"""

    permission_classes = [IsAuthenticated, IsBranchMember]
