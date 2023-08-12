from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    EditUserPermissionsForBranch,
    ListUsers,
    LoginView,
    LogoutView,
    UserBranchesView,
)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("branches/", UserBranchesView.as_view(), name="user_branches"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "user-branch-relations/", ListUsers.as_view(), name="list_user_branch_relations"
    ),
    path(
        "update-user-permissions/<uuid:pk>/",
        EditUserPermissionsForBranch.as_view(),
        name="edit_user_permissions_for_branch",
    ),
]
