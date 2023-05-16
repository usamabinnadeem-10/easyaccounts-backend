from rest_framework.permissions import IsAuthenticated

from .permissions import (
    IsAccountant,
    IsAdmin,
    IsAdminReadOnly,
    IsBranchMember,
    IsHeadAccountant,
    IsLoggedIn,
    IsPurchaser,
    IsSaleman,
    IsStockist,
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

    permission_classes = [IsAuthenticated, IsLoggedIn, IsAdmin | IsAccountant]


class IsAdminOrAccountantOrHeadAccountantMixin:
    """To check if user is admin or accountant"""

    permission_classes = [
        IsAuthenticated,
        IsLoggedIn,
        IsAdmin | IsAccountant | IsHeadAccountant,
    ]


class IsAdminOrReadAdminOrAccountantMixin:
    """To check if user is admin or read admin or accountant"""

    permission_classes = [
        IsAuthenticated,
        IsLoggedIn,
        IsAdmin | IsAdminReadOnly | IsAccountant,
    ]


class IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin:
    """To check if user is admin or read admin or accountant"""

    permission_classes = [
        IsAuthenticated,
        IsLoggedIn,
        IsAdmin | IsAdminReadOnly | IsAccountant | IsHeadAccountant,
    ]


class IsAdminOrReadAdminPermissionMixin:
    """To check if user is admin or read admin"""

    permission_classes = [IsAuthenticated, IsLoggedIn, IsAdmin | IsAdminReadOnly]


class IsAdminOrAccountantOrStockistMixin:
    """To check if user is admin or accountant or stockist"""

    permission_classes = [
        IsAuthenticated,
        IsLoggedIn,
        IsAdmin | IsAccountant | IsStockist,
    ]


class IsAdminOrStockistMixin:
    """To check if user is admin or stockist"""

    permission_classes = [IsAuthenticated, IsLoggedIn, IsAdmin | IsStockist]


class IsAdminOrReadAdminOrAccountantOrStockistPermissionMixin:
    """To check if user is admin or read admin or stockist"""

    permission_classes = [
        IsAuthenticated,
        IsLoggedIn,
        IsAdmin | IsAdminReadOnly | IsStockist | IsAccountant,
    ]
