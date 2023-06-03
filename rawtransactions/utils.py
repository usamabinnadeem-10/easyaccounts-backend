from collections import defaultdict
from operator import itemgetter

from django.db.models import Sum

from dying.models import DyingIssueDetail
from transactions.choices import TransactionChoices

from .models import RawDebitLotDetail, RawLotDetail, RawTransferLotDetail


def is_array_unique(array, key):
    uniques = defaultdict(lambda: True)
    for obj in array:
        value = uniques[obj[key]]
        if value:
            uniques[obj[key]] = None
        else:
            return False
    return True


def get_all_raw_stock(branch):
    balance_lots = list(
        (
            RawLotDetail.objects.values(
                "lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "lot_number__raw_product",
                "warehouse",
                # "formula",
            )
            .filter(lot_number__raw_transaction__branch=branch, lot_number__issued=False)
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_lots = list(
        map(
            lambda obj: {
                **obj,
                "nature": "C",
                "raw_product": obj["lot_number__raw_product"],
            },
            balance_lots,
        )
    )

    balance_debits = list(
        (
            RawDebitLotDetail.objects.values(
                "return_lot__lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "return_lot__lot_number__raw_product",
                "warehouse",
                # "formula",
                # "nature",
            )
            .filter(
                return_lot__bill_number__branch=branch,
                return_lot__lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_debits = list(
        map(
            lambda obj: {
                **obj,
                "nature": "D",
                "lot_number": obj["return_lot__lot_number"],
                "raw_product": obj["return_lot__lot_number__raw_product"],
            },
            balance_debits,
        )
    )

    balance_transfers = list(
        (
            RawTransferLotDetail.objects.values(
                "raw_transfer_lot__lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "raw_transfer_lot__lot_number__raw_product",
                "warehouse",
                "transferring_warehouse"
                # "formula",
                # "nature",
            )
            .filter(
                raw_transfer_lot__raw_transfer__branch=branch,
                raw_transfer_lot__lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_transfers_debits = list(
        map(
            lambda obj: {
                **obj,
                "warehouse": obj["transferring_warehouse"],
                "nature": "D",
                "lot_number": obj["raw_transfer_lot__lot_number"],
                "raw_product": obj["raw_transfer_lot__lot_number__raw_product"],
            },
            balance_transfers,
        )
    )
    balance_transfers_credits = list(
        map(
            lambda obj: {
                **obj,
                "nature": "C",
                "lot_number": obj["raw_transfer_lot__lot_number"],
                "raw_product": obj["raw_transfer_lot__lot_number__raw_product"],
            },
            balance_transfers,
        )
    )
    balance_transfers = [*balance_transfers_debits, *balance_transfers_credits]

    balance_dyings = list(
        (
            DyingIssueDetail.objects.values(
                "dying_lot_number__lot_number__raw_product",
                "dying_lot_number__lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "formula",
                "warehouse",
            )
            .filter(
                dying_lot_number__dying_lot__dying_unit__branch=branch,
                dying_lot_number__lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_dyings = list(
        map(
            lambda obj: {
                **obj,
                "nature": "D",
                "raw_product": obj["dying_lot_number__lot_number__raw_product"],
                "lot_number": obj["dying_lot_number__lot_number"],
            },
            balance_dyings,
        )
    )
    return [*balance_lots, *balance_debits, *balance_dyings, *balance_transfers]


def get_current_stock_position(branch):
    stock_array = get_all_raw_stock(branch)
    d = defaultdict(lambda: defaultdict(int))

    group_keys = [
        "actual_gazaana",
        "expected_gazaana",
        "raw_product",
        "warehouse",
        "lot_number",
    ]
    sum_keys = ["quantity"]

    for item in stock_array:
        for key in sum_keys:
            if item["nature"] == TransactionChoices.CREDIT:
                d[itemgetter(*group_keys)(item)][key] += item[key]
            else:
                d[itemgetter(*group_keys)(item)][key] -= item[key]

    stock = [{**dict(zip(group_keys, k)), **v} for k, v in d.items()]
    return stock
