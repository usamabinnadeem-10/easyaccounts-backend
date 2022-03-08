from django.db import models


class RoleChoices(models.TextChoices):
    ACCOUNTANT = "accountant", "Accountant"
    ADMIN = "admin", "Admin"
