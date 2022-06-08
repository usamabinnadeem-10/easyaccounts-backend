from django_filters.rest_framework import DjangoFilterBackend
from essentials.pagination import CustomPagination
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser

from .queries import PaymentQuery
from .serializers import PaymentSerializer


class ListPaymentView(PaymentQuery, ListAPIView):
    """
    list and filter payments
    """

    serializer_class = PaymentSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte", "exact"],
        "user": ["exact"],
        "person": ["exact"],
        "amount": ["gte", "lte", "exact"],
        "nature": ["exact"],
    }


class CreatePaymentView(PaymentQuery, CreateAPIView):
    """create payments"""

    parser_classes = [MultiPartParser, FormParser]
    serializer_class = PaymentSerializer
