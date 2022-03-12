from django.db import models


class RoleChoices(models.TextChoices):
    ACCOUNTANT = "accountant", "Accountant"
    ADMIN = "admin", "Admin"
    SALEMAN = "saleman", "Saleman"
    PURCHASER = "purchaser", "Purchaser"
