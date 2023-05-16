from django.db import models


class RoleChoices(models.TextChoices):
    ACCOUNTANT = "accountant", "Accountant"
    HEAD_ACCOUNTANT = "head_accountant", "Head Accountant"
    ADMIN = "admin", "Admin"
    SALEMAN = "saleman", "Saleman"
    PURCHASER = "purchaser", "Purchaser"
    STOCKIST = "stockist", "Stockist"
    ADMIN_VIEWER = "admin_viewer", "Admin Viewer"
