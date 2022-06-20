from collections import defaultdict
from datetime import datetime
from functools import reduce

from authentication.models import BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial

# from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg, Sum
from essentials.models import AccountType, Person, Product, Stock, Warehouse
from ledgers.models import Ledger
from payments.models import Payment
from rest_framework.serializers import ValidationError

from .choices import TransactionChoices, TransactionSerialTypes, TransactionTypes


class Transaction(ID, UserAwareModel, DateTimeAwareModel, NextSerial):
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    discount = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    serial = models.PositiveBigIntegerField()
    detail = models.CharField(max_length=1000, null=True)
    account_type = models.ForeignKey(AccountType, null=True, on_delete=models.SET_NULL)
    paid_amount = models.FloatField(default=0.0)
    # manual_invoice_serial = models.BigIntegerField()
    serial_type = models.CharField(max_length=3, choices=TransactionSerialTypes.choices)
    requires_action = models.BooleanField(default=False)
    builty = models.CharField(max_length=100, null=True, default=None)

    class Meta:
        ordering = ["serial"]

    # returns serial like SUP-123, INV-1453 ...
    # def get_manual_serial(self):
    #     return f"{self.manual_serial_type}-{self.manual_invoice_serial}"

    def get_computer_serial(self):
        return f"{self.serial_type}-{self.serial}"

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
                filter(lambda x: str(x["product"]) == str(d["product"].id), averages)
            )

            if len(curr_avg) == 0:
                return
            if d["rate"] <= curr_avg[0]["avg_buying"]:
                raise ValidationError(f"Rate too low for {d['product']}", 400)

    @classmethod
    def get_all_stock(cls, branch, date, t_new=None, t_old=None, **kwargs):
        """complete current stock, accepts kwrags for filtering transaction detail"""
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
        transfers = (
            StockTransferDetail.objects.values(
                "product", "to_warehouse", "yards_per_piece", "transfer__from_warehouse"
            )
            # .filter(transfer__date__lte=date)
            .annotate(quantity=Sum("quantity"))
        )
        for t in transfers:
            product = {
                "product": t["product"],
                "yards_per_piece": t["yards_per_piece"],
                "quantity": t["quantity"],
            }
            opening.append(
                {
                    "warehouse": t["transfer__from_warehouse"],
                    "transaction__nature": "D",
                    **product,
                }
            )
            opening.append(
                {
                    "warehouse": t["to_warehouse"],
                    "transaction__nature": "C",
                    **product,
                }
            )
        if t_old and t_new:
            stock_raw = (
                TransactionDetail.objects.values(
                    "product", "warehouse", "yards_per_piece", "transaction__nature"
                )
                .filter(transaction__branch=branch, transaction__date__lte=date, **kwargs)
                .exclude(transaction=t_old)
                .annotate(quantity=Sum("quantity"))
            )
            new_detail_array = []
            for new_det in t_new["transaction_detail"]:
                new_detail_array.append(
                    {
                        "quantity": new_det["quantity"],
                        "product": new_det["product"].id,
                        "warehouse": new_det["warehouse"].id,
                        "yards_per_piece": new_det["yards_per_piece"],
                        "transaction__nature": t_new["nature"],
                    }
                )
            stock_raw = [*stock_raw, *new_detail_array, *opening]
        else:
            stock_raw = (
                TransactionDetail.objects.values(
                    "product", "warehouse", "yards_per_piece", "transaction__nature"
                )
                .filter(
                    transaction__person__branch=branch,
                    # transaction__date__lte=date,
                    **kwargs,
                )
                .annotate(quantity=Sum("quantity"))
            )
            stock_raw = [*stock_raw, *opening]

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
    def check_stock(cls, branch, date=None, t_new=None, t_old=None):
        """checks if the stock is valid"""
        stock = Transaction.get_all_stock(branch, date, t_new, t_old)
        for s in stock:
            if s["quantity"] < 0:
                product = Product.objects.get(id=s["product"])
                raise ValidationError(f"{product.name} low in stock", 400)

    @classmethod
    def make_transaction(cls, data, request, old=None):
        """make a transaction"""
        user = request.user
        branch = request.branch
        if user and branch:
            transaction_details = data.pop("transaction_detail")
            paid = data.pop("paid")
            if paid and data["paid_amount"] <= 0.0:
                raise ValidationError(
                    "Please enter a valid paid amount",
                    400,
                )
            if data["serial_type"] in [
                TransactionSerialTypes.INV,
                TransactionSerialTypes.MWC,
            ]:
                Transaction.check_average_selling_rates(data["date"], transaction_details)
            if old:
                old.delete()

            transaction = Transaction.objects.create(
                user=user,
                **data,
                serial=Transaction.get_next_serial(
                    "serial",
                    serial_type=data["serial_type"],
                    person__branch=branch,
                ),
            )
            details = []

            # verify if the selling rates are legal
            for detail in transaction_details:
                # if TransactionDetail.is_rate_invalid(
                #     transaction.nature, detail["product"], detail["rate"]
                # ):
                #     raise ValidationError(
                #         f"Rate too low for {detail['product'].name}",
                #         400,
                #     )
                details.append(
                    TransactionDetail(
                        transaction_id=transaction.id,
                        **detail,
                    )
                )
            transactions = TransactionDetail.objects.bulk_create(details)

            # check if the stock is okay
            Transaction.check_stock(branch)

            # create ledger entry for the current transaction
            Ledger.create_ledger_entry_for_transasction(
                {"transaction": transaction, "detail": transaction_details}
            )

            # if the transaction is paid then create a payment entry
            # if paid:
            #     Payment.make_payment(
            #         request,
            #         {
            #             "nature": TransactionChoices.CREDIT,
            #             "amount": transaction.paid_amount,
            #             "account_type": transaction.account_type,
            #             "person": transaction.person,
            #         },
            #     )

            return {"transaction": transaction, "detail": transactions}
        raise ValidationError(
            "No user / branch found",
            400,
        )

    def get_transaction_string(self, nature):
        """Return string for ledger. Instances here are LedgerAndTransaction records"""
        string = ""
        transaction = self
        details = transaction.transaction_detail.all()
        serial_type = transaction.serial_type
        serial_num = transaction.get_computer_serial()
        if serial_type == TransactionSerialTypes.INV:
            if nature == TransactionChoices.CREDIT:
                if self.account_type is not None:
                    return f"Paid for {serial_num} against {self.account_type.name}"
                else:
                    return f"Paid for {serial_num}"
            else:
                # return f"Paid for {serial_num}"
                string += "Sale : "
        elif serial_type == TransactionSerialTypes.SUP:
            string += "Purchase : "
        elif serial_type == TransactionSerialTypes.MWC:
            string += "Purchase return : "
        elif serial_type == TransactionSerialTypes.MWS:
            string += "Sale return : "
        # string += f" {serial_num} : "
        for d in details:
            string += (
                f"{float(d.quantity)} thaan "
                f"{d.product.name} ({d.yards_per_piece} Yards) "
                f"@ PKR {str(d.rate)} per yard\n"
            )
        return string


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


# class CancelledInvoice(BranchAwareModel, UserAwareModel, NextSerial):
#     manual_invoice_serial = models.BigIntegerField()
#     manual_serial_type = models.CharField(
#         max_length=3, choices=TransactionSerialTypes.choices
#     )
#     comment = models.CharField(max_length=500)

#     class Meta:
#         unique_together = (
#             "manual_invoice_serial",
#             "manual_serial_type",
#             "branch",
#         )

#     # returns serial like SUP-123, INV-1453 ...
#     def get_manual_serial(self):
#         return f"{self.manual_serial_type}-{self.manual_invoice_serial}"


# class CancelStockTransfer(ID, UserAwareModel, NextSerial):
#     warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
#     manual_invoice_serial = models.PositiveBigIntegerField()


class StockTransfer(BranchAwareModel, UserAwareModel, DateTimeAwareModel, NextSerial):
    serial = models.PositiveBigIntegerField()
    # manual_invoice_serial = models.PositiveBigIntegerField()
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="from_warehouse", default=None
    )

    class Meta:
        unique_together = ["serial", "from_warehouse"]

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
