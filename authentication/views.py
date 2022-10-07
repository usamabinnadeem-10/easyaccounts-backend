from rest_framework.generics import CreateAPIView, ListAPIView

from .mixins import (
    HasBranchPermissionMixin,
    IsAdminOrReadAdminPermissionMixin,
    IsAuthenticatedPermissionMixin,
)
from .queries import UserBranchQuery, UserQuery
from .serializers import (
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
