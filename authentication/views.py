from rest_framework.generics import ListAPIView, CreateAPIView

from .mixins import IsAuthenticatedPermissionMixin
from .queries import UserBranchQuery
from .serializers import UserBranchSerializer, LoginSerializer


class UserBranchesView(UserBranchQuery, ListAPIView, IsAuthenticatedPermissionMixin):
    """get all the branches user is a part of"""

    serializer_class = UserBranchSerializer


class LoginView(CreateAPIView, IsAuthenticatedPermissionMixin):
    """log the user inside the branch"""

    serializer_class = LoginSerializer
