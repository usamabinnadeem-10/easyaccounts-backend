from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response

from authentication.mixins import (
    IsAdminOrAccountantMixin,
    IsAdminOrAccountantOrHeadAccountantMixin,
    IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin,
    IsAdminPermissionMixin,
)
from core.pagination import StandardPagination
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .queries import PaymentImageQuery, PaymentQuery
from .serializers import (
    PaymentAndImageListSerializer,
    PaymentSerializer,
    UploadImageSerializer,
)


class ListPaymentView(
    PaymentQuery, IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin, ListAPIView
):
    """
    list and filter payments
    """

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


class CreatePaymentView(
    PaymentQuery, IsAdminOrAccountantOrHeadAccountantMixin, CreateAPIView, UpdateAPIView
):
    """create payments"""

    serializer_class = PaymentSerializer


class UpdatePaymentView(
    PaymentQuery, IsAdminOrAccountantOrHeadAccountantMixin, UpdateAPIView
):
    """update payments"""

    serializer_class = PaymentSerializer


class DeletePaymentView(
    PaymentQuery, IsAdminOrAccountantOrHeadAccountantMixin, DestroyAPIView
):
    """delete payments"""

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        log_string = (
            f"""P-{instance.serial}:\n"""
            f"""{instance.amount}/= {instance.get_nature_display()} """
            f"""{instance.person.name} {instance.date}"""
            f"""{f" on {instance.account_type.name}" if instance.account_type else ""}"""
        )
        Log.create_log(
            ActivityTypes.DELETED,
            ActivityCategory.PAYMENT,
            log_string,
            request,
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddImageView(PaymentImageQuery, IsAdminOrAccountantMixin, CreateAPIView):
    """add images only"""

    serializer_class = UploadImageSerializer


class DeletePictureView(PaymentImageQuery, IsAdminPermissionMixin, DestroyAPIView):
    pass
