from django.db import models


class ChequeStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    TRANSFERRED = "transferred", "Transferred"
    CLEARED = "cleared", "Cleared"
    RETURNED = "returned", "Returned"
    COMPLETED_HISTORY = "completed_history", "Completed History"
    COMPLETED_TRANSFER = "completed_transfer", "Completed Transfer"


class PersonalChequeStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    CLEARED = "cleared", "Cleared"
    RETURNED = "returned", "Returned"
    CANCELLED = "cancelled", "Cancelled"


class BankChoices(models.TextChoices):
    MEEZAN = "meezan", "Meezan Bank"
    AL_BARAKA = "al_baraka", "Al Baraka Bank"
    HABIB_METRO = "habib_metro", "Habib Metropolitan Bank"
    ASKARI = "askari", "Askari Bank"
    ALLIED = "allied", "Allied Bank"
    ALFALAH = "alfalah", "Bank Alfalah"
    AL_HABIB = "al_habib", "Bank Al-Habib"
    DUBAI_ISLAMI = "dubai_islami", "Dubai Bank Islami"
    CITI = "citi", "Citi Bank"
    BANK_ISLAMI = "islami", "Bank Islami"
    FAYSAL = "faysal", "Faysal Bank"
    FIRST_WOMAN = "first_woman", "First Women Bank"
    HBL = "hbl", "Habib Bank Limited"
    STANDARD_CHARTERED = "standard_chartered", "Standard Chartered Bank"
    JS = "js", "JS Bank Limited"
    MCB = "mcb", "MCB Bank Limited"
    MCB_ISLAMIC = "mcb_islamic", "MCB Islamic Bank Limited"
    NATIONAL = "national", "National Bank of Pakistan"
    UBL = "ubl", "ubl"
