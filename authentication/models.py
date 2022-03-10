from django.db import models
from django.contrib.auth.models import User

from .choices import RoleChoices
from .managers import UserBranchManager

from uuid import uuid4


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return self.name


class UserBranchRelation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=RoleChoices.choices, default=RoleChoices.ACCOUNTANT
    )
    is_logged_in = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    utils = UserBranchManager()

    def login(self):
        self.is_logged_in = True
        self.save()

    def logout(self):
        self.is_logged_in = False
        self.save()


class BranchAwareModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    branch = models.ForeignKey(
        Branch, related_name="%(class)s", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
