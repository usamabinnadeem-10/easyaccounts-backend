from django.db import models


class ExpenseTypes(models.TextChoices):
    RENT = "rent", "Rent"
    ELECTRICITY = "electricity", "Electricity"
    MAINTENANCE = "maintenance", "Maintenance"
    SALARY = (
        "salary",
        "Salary",
    )
    TRANSPORTATION = (
        "transportation",
        "Transportation",
    )
    ADMINISTRATIVE = (
        "administrative",
        "Administrative",
    )
    MARKETING = (
        "marketing",
        "Marketing",
    )
    REFRESHMENT = (
        "refreshments",
        "Refreshments",
    )
    SPECIAL = (
        "special",
        "Special",
    )
    COMMISSION = (
        "commission",
        "Commission",
    )
    PRINTING = (
        "printing",
        "Printing",
    )
    LEGAL = (
        "legal",
        "Legal",
    )
    COMMUNICATION = (
        "communication",
        "Communication",
    )
    TAXATION = (
        "taxation",
        "Taxation",
    )
    SOFTWARE = (
        "software",
        "Software",
    )
    OTHER = (
        "other",
        "Other",
    )
