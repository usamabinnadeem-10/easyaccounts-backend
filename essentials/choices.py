from django.db import models

SUPPLIER = "S"
CUSTOMER = "C"


class PersonChoices(models.TextChoices):
    SUPPLIER = SUPPLIER, "Supplier"
    CUSTOMER = CUSTOMER, "Customer"


CHEQUE_ACCOUNT = "cheque_account"


class LinkedAccountChoices(models.TextChoices):
    CHEQUE_ACCOUNT = CHEQUE_ACCOUNT, "cheque_account"
