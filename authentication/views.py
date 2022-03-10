from rest_framework.generics import ListAPIView, CreateAPIView

from .mixins import IsAuthenticatedPermissionMixin, HasBranchPermissionMixin
from .queries import UserBranchQuery
from .serializers import UserBranchSerializer, LoginSerializer, LogoutSerializer


class UserBranchesView(HasBranchPermissionMixin, UserBranchQuery, ListAPIView):
    """get all the branches user is a part of"""

    serializer_class = UserBranchSerializer


class LoginView(IsAuthenticatedPermissionMixin, CreateAPIView):
    """log the user inside the branch"""

    serializer_class = LoginSerializer


class LogoutView(IsAuthenticatedPermissionMixin, CreateAPIView, UserBranchQuery):
    """log user out of all branches"""

    serializer_class = LogoutSerializer
