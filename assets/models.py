from authentication.models import BranchAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import DateTimeAwareModel
from django.core.validators import MinValueValidator
from django.db import models

from .choices import AssetStatusChoices, AssetTypeChoices


class Asset(BranchAwareModel, DateTimeAwareModel):

    name = models.CharField(max_length=100)
    value = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    status = models.CharField(max_length=15, choices=AssetStatusChoices.choices)
    type = models.CharField(max_length=15, choices=AssetTypeChoices.choices)

    def __str__(self):
        return self.name
