from django.db import models


class ActivityTypes(models.TextChoices):
    CREATED = "C", "Created"
    EDITED = "E", "Edited"
    DELETED = "D", "Deleted"


class ActivityCategory(models.TextChoices):
    TRANSACTION = "transaction", "Transaction"
    CANCELLED_TRANSACTION = "cancelled_transaction", "Cancelled Transaction"
    EXPENSE = "expense", "Expense"
    LEDGER_ENTRY = "ledger_entry", "Ledger entry"
    EXTERNAL_CHEQUE = "external_cheque", "External cheque"
    EXTERNAL_CHEQUE_HISTORY = "external_cheque_history", "External cheque history"
    PERSONAL_CHEQUE = "personal_cheque", "External cheque"
    PERSONAL_CHEQUE_HISTORY = "personal_cheque_history", "Personal cheque history"
    STOCK_TRANSFER = "stock_transfer", "Stock transfer"
    CANCELLED_STOCK_TRANSFER = "cancelled_stock_transfer", "Cancelled stock transfer"
    PERSON = "person", "Person"
    ACCOUNT_TYPE = "account_type", "Account type"
    WAREHOUSE = "warehouse", "Warehouse"
    PRODUCT = "product", "Product"
    PRODUCT_CATEGORY = "product_category", "Product category"
    AREA = "area", "Area"
