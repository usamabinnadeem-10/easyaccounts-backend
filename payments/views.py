from core.pagination import StandardPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)

# from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentImage
from .queries import PaymentAndImageQuery, PaymentImageQuery, PaymentQuery
from .serializers import (
    PaymentAndImageListSerializer,
    PaymentSerializer,
    UploadImageSerializer,
)


class ListPaymentView(PaymentQuery, ListAPIView):
    """
    list and filter payments
    """

    # parser_classes = [MultiPartParser, FormParser]
    serializer_class = PaymentAndImageListSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte", "exact"],
        "user": ["exact"],
        "person": ["exact"],
        "account_type": ["exact"],
        "amount": ["gte", "lte", "exact"],
        "nature": ["exact"],
    }


class CreatePaymentView(PaymentQuery, CreateAPIView, UpdateAPIView):
    """create payments"""

    serializer_class = PaymentSerializer


class UpdatePaymentView(PaymentQuery, UpdateAPIView):
    """update payments"""

    serializer_class = PaymentSerializer


class DeletePaymentView(PaymentQuery, DestroyAPIView):
    """delete payments"""

    pass


class AddImageView(PaymentImageQuery, CreateAPIView):
    """add images only"""

    serializer_class = UploadImageSerializer


class DeletePictureView(PaymentImageQuery, DestroyAPIView):
    pass
