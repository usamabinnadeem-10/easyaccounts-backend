from authentication.models import BranchAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import DateTimeAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum

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
    sold_date = models.DateTimeField(default=None, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_total_assets(cls, branch, date=None):
        date_filter = {"date__lte": date} if date else {}
        return (
            Asset.objects.filter(
                branch=branch, status=AssetStatusChoices.PURCHASED, **date_filter
            ).aggregate(total=Sum("value"))["total"]
            or 0
        )

    @classmethod
    def get_total_asset_profit(cls, branch, end_date=None, start_date=None):
        date_filter = {"sold_date__lte": end_date} if end_date else {}
        if start_date:
            date_filter.update({"sold_date__gte": start_date})
        return (
            Asset.objects.filter(
                status=AssetStatusChoices.SOLD, branch=branch, **date_filter
            ).aggregate(total=Sum(F("sold_value") - F("value")))["total"]
            or 0
        )
