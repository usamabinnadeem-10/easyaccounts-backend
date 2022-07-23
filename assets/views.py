from authentication.mixins import (
    IsAdminOrReadAdminPermissionMixin,
    IsAdminPermissionMixin,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)

from .queries import AssetQuery
from .serializers import AssetSerializer


class CreateAsset(IsAdminPermissionMixin, AssetQuery, CreateAPIView):
    """
    create Asset
    """

    serializer_class = AssetSerializer


class ListAsset(IsAdminOrReadAdminPermissionMixin, AssetQuery, ListAPIView):
    """
    list Assets
    """

    serializer_class = AssetSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte", "exact"],
        "status": ["exact"],
        "type": ["exact"],
        "value": ["gte", "lte", "exact"],
        "name": ["icontains"],
    }


class EditAsset(IsAdminPermissionMixin, AssetQuery, UpdateAPIView):
    """
    edit an Asset
    """

    serializer_class = AssetSerializer


class DeleteAsset(IsAdminPermissionMixin, AssetQuery, DestroyAPIView):
    """
    delete an Asset
    """

    serializer_class = AssetSerializer
