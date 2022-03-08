from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedPermissionMixin:
    """This mixin is used wherever IsAuthenticated permission is required."""

    permission_classes = [
        IsAuthenticated,
    ]
