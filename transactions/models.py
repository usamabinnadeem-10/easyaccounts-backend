from collections import defaultdict
from datetime import datetime
from functools import reduce

from authentication.models import BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg, Sum
from essentials.models import AccountType, Person, Product, Stock, Warehouse
from ledgers.models import Ledger

from .choices import TransactionChoices, TransactionSerialTypes, TransactionTypes


class Transaction(BranchAwareModel, UserAwareModel, DateTimeAwareModel, NextSerial):
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    discount = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    serial = models.PositiveBigIntegerField()
    detail = models.CharField(max_length=1000, null=True)
    account_type = models.ForeignKey(AccountType, null=True, on_delete=models.SET_NULL)
    paid_amount = models.FloatField(default=0.0)
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(
        max_length=3, choices=TransactionSerialTypes.choices
    )
    requires_action = models.BooleanField(default=False)
    builty = models.CharField(max_length=100, null=True, default=None)

    class Meta:
        ordering = ["serial"]
        unique_together = (
            "manual_invoice_serial",
            "manual_serial_type",
            "branch",
        )

    # returns serial like SUP-123, INV-1453 ...
    def get_manual_serial(self):
        return f"{self.manual_serial_type}-{self.manual_invoice_serial}"

    @classmethod
    def check_average_selling_rates(cls, date, t_detail):
        """check if selling rate is more than buying"""
        date = date if date else datetime.now()
        averages = (
            TransactionDetail.objects.values("product")
            .filter(
                transaction__date__lte=date, transaction__nature=TransactionChoices.CREDIT
            )
            .annotate(avg_buying=Avg("rate"))
        )
        for d in t_detail:
            curr_avg = list(
                filter(lambda x: x["product"] == t_detail["product"], averages)
            )
            if d["rate"] <= curr_avg["avg_buying"]:
                raise ValidationError(f"Rate too low for {d['product']}", 400)

    @classmethod
    def get_all_stock(cls, branch, date, old, **kwargs):
        """complete current stock"""
        date = date if date else datetime.now()
        opening = Stock.objects.values(
            "product", "warehouse", "yards_per_piece", "opening_stock"
        ).filter(product__category__branch=branch)
        opening = list(
            map(
                lambda x: {
                    **x,
                    "quantity": x["opening_stock"],
                    "transaction__nature": "C",
                },
                opening,
            )
        )
        stock_raw = (
            TransactionDetail.objects.values(
                "product", "warehouse", "yards_per_piece", "transaction__nature"
            )
            .filter(transaction__branch=branch, transaction__date__lte=date, **kwargs)
            .annotate(quantity=Sum("quantity"))
        )
        stock_raw = [*stock_raw, *opening]
        # if the transaction is being edited
        if old is not None:
            new_nature = (
                TransactionChoices.CREDIT
                if old.nature == TransactionChoices.DEBIT
                else TransactionChoices.DEBIT
            )
            old_details = TransactionDetail.objects.filter(transaction=old.id)
            for detail in old_details:
                stock_raw.append(
                    {
                        "product": detail.product,
                        "warehouse": detail.warehouse,
                        "yards_per_piece": detail.yards_per_piece,
                        "transaction__nature": new_nature,
                        "quantity": detail.quantity,
                    }
                )

        stock = defaultdict(int)
        for s in stock_raw:
            key = f"{s['product']}|{s['warehouse']}|{s['yards_per_piece']}"
            if s["transaction__nature"] == TransactionChoices.CREDIT:
                stock[key] += s["quantity"]
            else:
                stock[key] -= s["quantity"]
        final = []
        for key, value in stock.items():
            items = key.split("|")
            final.append(
                {
                    "quantity": value,
                    "product": items[0],
                    "warehouse": items[1],
                    "yards_per_piece": float(items[2]),
                }
            )
        return final

    @classmethod
    def check_stock(cls, branch, date, transaction_detail, old):
        """checks if the stock is valid"""
        stock = Transaction.get_all_stock(branch, date, old)
        for detail in transaction_detail:

            print(type(stock[0]["product"]))
            print(type(str(detail["product"].id)))
            print(stock[0]["product"] == detail["product"].id)
            filtered = list(
                filter(
                    lambda x: x["product"] == str(detail["product"].id)
                    and x["warehouse"] == str(detail["warehouse"].id)
                    and x["yards_per_piece"] == detail["yards_per_piece"],
                    stock,
                )
            )
            curr_stock = 0 if len(filtered) == 0 else filtered[0]["quantity"]
            if curr_stock - detail["quantity"] < 0:
                raise ValidationError(
                    f"{detail['product'].name} low in stock. Stock = {curr_stock}", 400
                )

    @classmethod
    def make_transaction(cls, data, user=None, branch=None, old=None):
        if user and branch:
            transaction_details = data.pop("transaction_detail")
            paid = data.pop("paid")
            if paid and data["paid_amount"] <= 0.0:
                raise ValidationError(
                    "Please enter a valid paid amount",
                    400,
                )
            if data["nature"] == TransactionChoices.DEBIT or old is not None:
                Transaction.check_stock(branch, data["date"], transaction_details, old)
                if data["type"] != TransactionTypes.PAID:
                    Transaction.check_average_selling_rates(
                        data["date"], transaction_details
                    )
            if old:
                old.delete()

            transaction = Transaction.objects.create(
                user=user,
                branch=branch,
                **data,
                serial=Transaction.get_next_serial(
                    branch,
                    "serial",
                    manual_serial_type=data["manual_serial_type"],
                ),
            )
            details = []
            for detail in transaction_details:
                if TransactionDetail.is_rate_invalid(
                    transaction.nature, detail["product"], detail["rate"]
                ):
                    raise ValidationError(
                        f"Rate too low for {detail['product'].name}",
                        400,
                    )
                details.append(
                    TransactionDetail(
                        transaction_id=transaction.id,
                        **detail,
                    )
                )
            transactions = TransactionDetail.objects.bulk_create(details)
            Ledger.create_ledger_entry_for_transasction(
                {"transaction": transaction, "detail": transaction_details, "paid": paid}
            )
            return {"transaction": transaction, "detail": transactions}
        raise ValidationError(
            "No user / branch found",
            400,
        )


class TransactionDetail(ID):
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="transaction_detail"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, name="product"
    )
    rate = models.FloatField(validators=[MinValueValidator(0.0)])
    yards_per_piece = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    quantity = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)

    @classmethod
    def is_rate_invalid(cls, nature, product, current_rate):
        if nature == TransactionChoices.DEBIT:
            return product.minimum_rate > current_rate
        return False


class CancelledInvoice(BranchAwareModel, UserAwareModel, NextSerial):
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(
        max_length=3, choices=TransactionSerialTypes.choices
    )
    comment = models.CharField(max_length=500)

    class Meta:
        unique_together = (
            "manual_invoice_serial",
            "manual_serial_type",
            "branch",
        )

    # returns serial like SUP-123, INV-1453 ...
    def get_manual_serial(self):
        return f"{self.manual_serial_type}-{self.manual_invoice_serial}"


class CancelStockTransfer(BranchAwareModel, UserAwareModel, NextSerial):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    manual_invoice_serial = models.PositiveBigIntegerField()


class StockTransfer(BranchAwareModel, UserAwareModel, DateTimeAwareModel, NextSerial):
    serial = models.PositiveBigIntegerField()
    manual_invoice_serial = models.PositiveBigIntegerField()
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="from_warehouse", default=None
    )

    class Meta:
        unique_together = ["serial", "manual_invoice_serial", "from_warehouse"]

    class Meta:
        verbose_name_plural = "Stock transfers"


class StockTransferDetail(ID):
    transfer = models.ForeignKey(
        StockTransfer, on_delete=models.CASCADE, related_name="transfer_detail"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    yards_per_piece = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="to_warehouse"
    )
    quantity = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])

    @classmethod
    def calculateTransferredAmount(cls, warehouse, product, filters):
        """return transferred amount to this warehouse"""
        custom_filters = {
            **filters,
            "product": product,
        }
        values = ["product", "from_warehouse", "to_warehouse"]
        quantity = 0.0
        transfers_in = (
            StockTransferDetail.objects.values(*values)
            .annotate(quantity=Sum("quantity"))
            .filter(
                **{
                    **custom_filters,
                    "to_warehouse": warehouse,
                }
            )
        )
        for t in transfers_in:
            quantity += t["quantity"]

        values[1] = "transfer__from_warehouse"
        transfers_out = (
            StockTransferDetail.objects.values(*values)
            .annotate(quantity=Sum("quantity"))
            .filter(
                **{
                    **custom_filters,
                    "transfer__from_warehouse": warehouse,
                }
            )
        )

        for t in transfers_out:
            quantity -= t["quantity"]

        return quantity
