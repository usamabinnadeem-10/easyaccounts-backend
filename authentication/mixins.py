from rest_framework.permissions import IsAuthenticated
from .permissions import IsBranchMember, IsAdmin, IsLoggedIn, IsPurchaser, IsSaleman


class IsAuthenticatedPermissionMixin:
    """To check if user is authenticated"""

    permission_classes = [
        IsAuthenticated,
    ]


class HasBranchPermissionMixin:
    """To check if the user is authenticated and is a member of at least one branch"""

    permission_classes = [IsAuthenticated, IsBranchMember]


class IsAdminPermissionMixin:
    """To check if the user is authenticated and is an admin"""

    permission_classes = [
        IsAuthenticated,
        IsLoggedIn,
        IsAdmin,
    ]


class IsPurchaserPermissionMixin:
    """To check if the user is authenticated and a purchaser"""

    permission_classes = [IsAuthenticated, IsLoggedIn, IsPurchaser]


class IsSalemanPermissionMixin:
    """To check if the user is authenticated and a saleman"""

    permission_classes = [IsAuthenticated, IsLoggedIn, IsSaleman]
