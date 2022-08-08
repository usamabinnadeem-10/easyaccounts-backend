from datetime import datetime

from authentication.models import BranchAwareModel, UserAwareModel
from django.db import models

from .choices import ActivityCategory, ActivityTypes


class Log(BranchAwareModel, UserAwareModel):
    time_stamp = models.DateTimeField(default=datetime.now)
    type = models.CharField(max_length=1, choices=ActivityTypes.choices)
    category = models.CharField(max_length=32, choices=ActivityCategory.choices)
    detail = models.TextField(max_length=1000)

    @classmethod
    def create_log(cls, type, category, detail, request):
        try:
            Log.objects.create(
                type=type,
                category=category,
                detail=detail,
                user=request.user,
                branch=request.branch,
            )
        except:
            raise ValueError("Could not create log because of missing kwargs")
