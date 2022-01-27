from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAcceptable

from essentials.models import Stock
from ledgers.models import Ledger


def is_low_quantity(stock_to_update, value):
    stock_in_hand = stock_to_update.stock_quantity - value
    if stock_in_hand < 0:
        raise NotAcceptable(
            f"""{stock_to_update.product.name} low in stock. Stock = {stock_to_update.stock_quantity}""",
            400,
        )


def create_ledger_entries(transaction, transaction_details, paid, ledger_string):
    amount = 0.0
    for t in transaction_details:
        amount += t["amount"]
    amount -= transaction.discount
    ledger_data = [
        Ledger(
            **{
                "detail": ledger_string,
                "amount": amount,
                "transaction": transaction,
                "nature": transaction.nature,
                "person": transaction.person,
                "date": transaction.date,
                "draft": transaction.draft,
            }
        )
    ]
    if paid:
        ledger_data.append(
            Ledger(
                **{
                    "detail": f"Paid on {transaction.account_type.name}",
                    "amount": transaction.paid_amount,
                    "transaction": transaction,
                    "nature": "C",
                    "account_type": transaction.account_type,
                    "person": transaction.person,
                    "date": transaction.date,
                    "draft": transaction.draft,
                }
            )
        )

    return ledger_data


def create_ledger_string(detail):
    return (
        f'{int(detail["quantity"])} thaan '
        f'{detail["product"].name} ({detail["yards_per_piece"]} Yards) '
        f'@ PKR {str(detail["rate"])} per yard\n'
    )


def update_stock(
    current_nature, detail, old_nature=None, is_update=False, old_quantity=0.0
):
    current_quantity = float(detail["quantity"])
    filters = {
        "product": detail["product"],
        "warehouse": detail["warehouse"],
        "yards_per_piece": detail["yards_per_piece"],
    }
    if current_nature == "C":
        stock_to_update, created = Stock.objects.get_or_create(**filters)
    else:
        stock_to_update = get_object_or_404(Stock, **filters)

    if is_update:

        adjustment_quantity = old_quantity if is_update else 0
        difference = (
            current_quantity - adjustment_quantity
        )  # difference between last and current transaction

        if current_nature == "C" and old_nature == "C":
            stock_to_update.stock_quantity += difference

        elif current_nature == "D" and old_nature == "D":
            is_low_quantity(stock_to_update, difference)
            stock_to_update.stock_quantity -= difference

        elif current_nature == "C" and old_nature == "D":
            stock_to_update.stock_quantity += current_quantity + old_quantity

        elif current_nature == "D" and old_nature == "C":
            is_low_quantity(stock_to_update, current_quantity + old_quantity)
            stock_to_update.stock_quantity -= current_quantity + old_quantity

    else:
        if current_nature == "C":
            stock_to_update.stock_quantity += current_quantity

        elif current_nature == "D":
            is_low_quantity(stock_to_update, current_quantity)
            stock_to_update.stock_quantity -= current_quantity

    stock_to_update.save()