from core.utils import convert_date_to_datetime
from django_filters.rest_framework import DjangoFilterBackend
from ledgers.models import Ledger
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from transactions.models import TransactionDetail

from .models import Asset
from .queries import AssetQuery
from .serializers import AssetSerializer


class CreateAsset(AssetQuery, CreateAPIView):
    """
    create Asset
    """

    serializer_class = AssetSerializer


class ListAsset(AssetQuery, ListAPIView):
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


class EditAsset(AssetQuery, UpdateAPIView):
    """
    edit an Asset
    """

    serializer_class = AssetSerializer


class DeleteAsset(AssetQuery, DestroyAPIView):
    """
    delete an Asset
    """

    serializer_class = AssetSerializer
