from core.pagination import StandardPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from .queries import LogQuery
from .serializers import LogSerializer


class LogView(LogQuery, ListAPIView):
    """
    list and filter logs
    """

    serializer_class = LogSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "time_stamp": ["gte", "lte"],
        "user": ["exact"],
        "detail": ["icontains"],
        "type": ["exact"],
        "category": ["exact"],
    }
