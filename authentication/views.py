from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView

from .mixins import (
    HasBranchPermissionMixin,
    IsAdminOrReadAdminPermissionMixin,
    IsAdminPermissionMixin,
    IsAuthenticatedPermissionMixin,
)
from .queries import UserBranchQuery, UserQuery
from .serializers import (
    EditUserPermissionsForBranchSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserBranchSerializer,
    UserSerializer,
)


class UserBranchesView(HasBranchPermissionMixin, UserBranchQuery, ListAPIView):
    """get all the branches user is a part of"""

    serializer_class = UserBranchSerializer


class LoginView(IsAuthenticatedPermissionMixin, CreateAPIView):
    """log the user inside the branch"""

    serializer_class = LoginSerializer


class LogoutView(IsAuthenticatedPermissionMixin, CreateAPIView, UserBranchQuery):
    """log user out of all branches"""

    serializer_class = LogoutSerializer


class ListUsers(IsAdminOrReadAdminPermissionMixin, UserQuery, ListAPIView):
    """List all users of the branch"""

    serializer_class = UserSerializer


class EditUserPermissionsForBranch(IsAdminPermissionMixin, UserQuery, UpdateAPIView):
    serializer_class = EditUserPermissionsForBranchSerializer
