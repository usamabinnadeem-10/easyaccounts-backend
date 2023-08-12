from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response

import authentication.constants as PERMISSIONS
from authentication.mixins import CheckPermissionsMixin
from core.pagination import StandardPagination
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .queries import PaymentImageQuery, PaymentQuery
from .serializers import (
    PaymentAndImageListSerializer,
    PaymentSerializer,
    UploadImageSerializer,
)


class ListPaymentView(PaymentQuery, CheckPermissionsMixin, ListAPIView):
    """
    list and filter payments
    """

    permissions = [PERMISSIONS.CAN_VIEW_PAYMENTS]
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
    PaymentQuery, CheckPermissionsMixin, CreateAPIView, UpdateAPIView
):
    """create payments"""

    permissions = [PERMISSIONS.CAN_CREATE_PAYMENT]
    serializer_class = PaymentSerializer


class UpdatePaymentView(PaymentQuery, CheckPermissionsMixin, UpdateAPIView):
    """update payments"""

    permissions = [PERMISSIONS.CAN_EDIT_PAYMENT]
    serializer_class = PaymentSerializer


class DeletePaymentView(PaymentQuery, CheckPermissionsMixin, DestroyAPIView):
    """delete payments"""

    permissions = [PERMISSIONS.CAN_DELETE_PAYMENT]

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


class AddImageView(PaymentImageQuery, CheckPermissionsMixin, CreateAPIView):
    """add images only"""

    permissions = [PERMISSIONS.CAN_CREATE_PAYMENT]
    serializer_class = UploadImageSerializer


class DeletePictureView(PaymentImageQuery, CheckPermissionsMixin, DestroyAPIView):
    permissions = [PERMISSIONS.CAN_DELETE_PAYMENT]
