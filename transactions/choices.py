from django.db import models


class TransactionChoices(models.TextChoices):
    CREDIT = "C", "Credit"
    DEBIT = "D", "Debit"


class TransactionTypes(models.TextChoices):
    MAAL_WAPSI = "maal_wapsi", "Maal Wapsi"
    PAID = "paid", "Paid"
    PURCHASE = "purchase", "Purchase"
    CREDIT = "credit", "Credit"
