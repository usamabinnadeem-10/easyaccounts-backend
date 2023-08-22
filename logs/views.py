from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

import authentication.constants as PERMISSIONS
from authentication.mixins import CheckPermissionsMixin
from core.pagination import LargePagination

from .queries import LogQuery
from .serializers import LogSerializer


class LogView(LogQuery, CheckPermissionsMixin, ListAPIView):
    """
    list and filter logs
    """

    permissions = [PERMISSIONS.CAN_VIEW_LOGS]
    serializer_class = LogSerializer
    pagination_class = LargePagination
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "time_stamp": ["gte", "lte"],
        "user": ["exact"],
        "detail": ["icontains"],
        "type": ["exact"],
        "category": ["exact"],
    }
