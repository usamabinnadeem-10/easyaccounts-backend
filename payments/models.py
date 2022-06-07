from authentication.models import UserAwareModel
from core.models import ID, DateTimeAwareModel
from django.db import models
from essentials.models import Person


# Create your models here.
class Payment(ID, DateTimeAwareModel, UserAwareModel):
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
