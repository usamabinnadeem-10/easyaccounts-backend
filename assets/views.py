from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)

import authentication.constants as PERMISSIONS
from authentication.mixins import CheckPermissionsMixin

from .queries import AssetQuery
from .serializers import AssetSerializer


class CreateAsset(CheckPermissionsMixin, AssetQuery, CreateAPIView):
    """
    create Asset
    """

    permissions = [PERMISSIONS.CAN_CREATE_ASSET]
    serializer_class = AssetSerializer


class ListAsset(CheckPermissionsMixin, AssetQuery, ListAPIView):
    """
    list Assets
    """

    permissions = [PERMISSIONS.CAN_VIEW_ASSETS]
    serializer_class = AssetSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte", "exact"],
        "status": ["exact"],
        "type": ["exact"],
        "value": ["gte", "lte", "exact"],
        "name": ["icontains"],
    }


class EditAsset(CheckPermissionsMixin, AssetQuery, UpdateAPIView):
    """
    edit an Asset
    """

    permissions = [PERMISSIONS.CAN_EDIT_ASSET]
    serializer_class = AssetSerializer


class DeleteAsset(CheckPermissionsMixin, AssetQuery, DestroyAPIView):
    """
    delete an Asset
    """

    permissions = [PERMISSIONS.CAN_DELETE_ASSET]
    serializer_class = AssetSerializer
