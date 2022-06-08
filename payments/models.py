from authentication.models import UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from django.core.validators import MinValueValidator
from django.db import models
from essentials.models import AccountType, Person
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


class PaymentImage(ID):
    image = models.ImageField(upload_to=get_image_upload_path)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
