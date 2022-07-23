from rest_framework.permissions import IsAuthenticated

from .permissions import (
    IsAccountant,
    IsAdmin,
    IsAdminReadOnly,
    IsBranchMember,
    IsLoggedIn,
    IsPurchaser,
    IsSaleman,
)


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


class IsAccountantPermissionMixin:
    """To check if the user is an accountant"""

    permission_classes = [IsAuthenticated, IsLoggedIn, IsAccountant]


class IsAdminOrAccountantMixin:
    """To check if user is admin or accountant"""

    permission_classes = [IsAdmin | IsAccountant, IsLoggedIn]


class IsAdminOrReadAdminOrAccountantMixin:
    """To check if user is admin or read admin or accountant"""

    permission_classes = [IsAdmin | IsAdminReadOnly | IsAccountant, IsLoggedIn]


class IsAdminOrReadAdminPermissionMixin:
    """To check if user is admin or read admin"""

    permission_classes = [IsAdmin | IsAdminReadOnly, IsLoggedIn]
