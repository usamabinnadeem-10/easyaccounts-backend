from django.db import models


# Al Baraka Bank (Pakistan) Limited
# Allied Bank Limited
# Askari Bank
# Bank Alfalah Limited
# Bank Al-Habib Limited
# BankIslami Pakistan Limited
# Citi Bank
# Deutsche Bank A.G
# The Bank of Tokyo-Mitsubishi UFJ
# Dubai Islamic Bank Pakistan Limited
# Faysal Bank Limited
# First Women Bank Limited
# Habib Bank Limited
# Standard Chartered Bank (Pakistan) Limited
# Habib Metropolitan Bank Limited
# Industrial and Commercial Bank of China
# Industrial Development Bank of Pakistan
# JS Bank Limited
# MCB Bank Limited
# MCB Islamic Bank Limited
# Meezan Bank Limited
# National Bank of Pakistan


class ChequeStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    TRANSFERRED = "transferred", "Transferred"
    CLEARED = "cleared", "Cleared"
    RETURNED = "returned", "Returned"


class PersonalChequeStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    CLEARED = "cleared", "Cleared"
    RETURNED = "returned", "Returned"
    CANCELLED = "cancelled", "Cancelled"


class BankChoices(models.TextChoices):
    MEEZAN = "meezan", "Meezan Bank Limited"
    AL_BARAKA = "al_baraka", "Al Baraka Bank (Pakistan) Limited"
    HABIB_METRO = "habib_metro", "Habib Metropolitan Bank Limited"
