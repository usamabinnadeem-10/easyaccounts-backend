from datetime import datetime
from uuid import uuid4

from django.db import models
from django.db.models import Max


class ID(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    class Meta:
        abstract = True


class DateTimeAwareModel(models.Model):
    """Provides date and time"""

    date = models.DateTimeField(default=datetime.now)

    class Meta:
        abstract = True


class NextSerial:
    @classmethod
    def get_next_serial(cls, branch, field, **kwargs):
        return (
            cls.objects.filter(branch=branch, **kwargs).aggregate(max_serial=Max(field))[
                "max_serial"
            ]
            or 0
        ) + 1
