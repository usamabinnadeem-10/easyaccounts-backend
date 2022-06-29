from django.db import models

SUPPLIER = "S"
CUSTOMER = "C"
EQUITY = "E"


class PersonChoices(models.TextChoices):
    SUPPLIER = SUPPLIER, "Supplier"
    CUSTOMER = CUSTOMER, "Customer"
    EQUITY = EQUITY, "Equity"


CHEQUE_ACCOUNT = "cheque_account"


class LinkedAccountChoices(models.TextChoices):
    CHEQUE_ACCOUNT = CHEQUE_ACCOUNT, "cheque_account"
