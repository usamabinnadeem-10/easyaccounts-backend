from django.db import models
from django.contrib.auth.models import User

from .choices import RoleChoices

from uuid import uuid4


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)


class UserBranchRelation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=RoleChoices.choices, default=RoleChoices.ACCOUNTANT
    )
    is_logged_in = models.BooleanField(default=False)

    def login(self):
        self.is_logged_in = True
        self.save()

    def logout(self):
        self.is_logged_in = False
        self.save()
