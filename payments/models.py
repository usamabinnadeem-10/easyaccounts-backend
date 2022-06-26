from authentication.models import UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from django.core.validators import MinValueValidator
from django.db import models
from easyaccounts.storage_backends import PrivateMediaStorage
from essentials.models import AccountType, Person
from ledgers.models import LedgerAndPayment
from transactions.choices import TransactionChoices

from .utils import get_image_upload_path


class Payment(ID, DateTimeAwareModel, UserAwareModel, NextSerial):
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    account_type = models.ForeignKey(
        AccountType, on_delete=models.PROTECT, null=True, default=None
    )
    amount = models.FloatField(validators=[MinValueValidator(1.0)])
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    serial = models.PositiveBigIntegerField()
    detail = models.CharField(max_length=1000, null=True)

    def get_ledger_string(self):
        """Return string for ledger. Instances here are LedgerAndPayment records"""
        string = ""
        account_type = f" : ({self.account_type.name})" if self.account_type else ""
        detail = f" {self.detail}" if self.detail is not None else ""
        string += f"Payment{account_type}{detail}"
        return string

    @classmethod
    def _create_payment(cls, request, validated_data):
        serial = Payment.get_next_serial("serial", person__branch=request.branch)
        payment_instance = Payment.objects.create(
            user=request.user, serial=serial, **validated_data
        )
        return payment_instance

    @classmethod
    def make_payment(cls, request, validated_data):
        payment_instance = Payment._create_payment(request, validated_data)
        LedgerAndPayment.create_ledger_entry(payment_instance)
        return payment_instance


class PaymentImage(ID):
    image = models.ImageField(
        upload_to=get_image_upload_path, storage=PrivateMediaStorage()
    )


class PaymentAndImage(ID):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    image = models.ForeignKey(
        PaymentImage, on_delete=models.CASCADE, related_name="payment_image"
    )
