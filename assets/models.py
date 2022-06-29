from authentication.models import BranchAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import DateTimeAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from .choices import AssetStatusChoices, AssetTypeChoices


class Asset(BranchAwareModel, DateTimeAwareModel):

    name = models.CharField(max_length=100)
    value = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    status = models.CharField(max_length=15, choices=AssetStatusChoices.choices)
    type = models.CharField(max_length=15, choices=AssetTypeChoices.choices)
    sold_value = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)],
        default=None,
        null=True,
    )

    def __str__(self):
        return self.name

    @classmethod
    def get_total_assets(cls, branch, date=None):
        date_filter = {"date": date} if date else {}
        return (
            Asset.objects.filter(
                branch=branch, status=AssetStatusChoices.PURCHASED, **date_filter
            ).aggregate(total=Sum("value"))["total"]
            or 0
        )
