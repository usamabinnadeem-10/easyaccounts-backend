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
                "lot_number__lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "lot_number__raw_product",
                "lot_number__product_glue",
                "lot_number__product_type",
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
                "lot_number": obj["lot_number__lot_number"],
                "nature": "C",
                "raw_product": obj["lot_number__raw_product"],
                "product_glue": obj["lot_number__product_glue"],
                "product_type": obj["lot_number__product_type"],
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
                "return_lot__raw_product",
                "return_lot__product_glue",
                "return_lot__product_type",
                "warehouse",
                "return_lot__bill_number__debit_type",
                # "nature",
            )
            .filter(
                return_lot__bill_number__branch=branch,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_debits = list(
        map(
            lambda obj: {
                **obj,
                "nature": "C"
                if obj["return_lot__bill_number__debit_type"] == "sale_return"
                else "D",
                "lot_number": obj["return_lot__lot_number"],
                "raw_product": obj["return_lot__raw_product"],
                "product_glue": obj["return_lot__product_glue"],
                "product_type": obj["return_lot__product_type"],
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
                "raw_transfer_lot__raw_product",
                "raw_transfer_lot__product_glue",
                "raw_transfer_lot__product_type",
                "warehouse",
                "transferring_warehouse",
            )
            .filter(
                raw_transfer_lot__raw_transfer__branch=branch,
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
                "raw_product": obj["raw_transfer_lot__raw_product"],
                "product_glue": obj["raw_transfer_lot__product_glue"],
                "product_type": obj["raw_transfer_lot__product_type"],
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
                "raw_product": obj["raw_transfer_lot__raw_product"],
                "product_glue": obj["raw_transfer_lot__product_glue"],
                "product_type": obj["raw_transfer_lot__product_type"],
            },
            balance_transfers,
        )
    )
    balance_transfers = [*balance_transfers_debits, *balance_transfers_credits]

    balance_dyings = list(
        (
            DyingIssueDetail.objects.values(
                "dying_issue_lot__raw_lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "warehouse",
            )
            .filter(
                dying_issue_lot__dying_issue__branch=branch,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_dyings = list(
        map(
            lambda obj: {
                **obj,
                "nature": "D",
                "raw_product": next(
                    (
                        lot["raw_product"]
                        for lot in balance_lots
                        if balance_lots["lot_number"]
                        == obj["dying_issue_lot__raw_lot_number"]
                    ),
                    None,
                ),
                "lot_number": obj["dying_issue_lot__raw_lot_number"],
            },
            balance_dyings,
        )
    )
    return [*balance_lots, *balance_debits, *balance_transfers, *balance_dyings]
    # return [*balance_lots, *balance_debits, *balance_dyings, *balance_transfers]


def get_current_stock_position(branch):
    stock_array = get_all_raw_stock(branch)
    d = defaultdict(lambda: defaultdict(int))

    group_keys = [
        "actual_gazaana",
        "expected_gazaana",
        "raw_product",
        "warehouse",
        "lot_number",
        "product_glue",
        "product_type",
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


def validate_raw_inventory(branch):
    stock = get_current_stock_position(branch)
    for s in stock:
        if s["quantity"] < 0:
            return False, f"Low stock for lot # {s['lot_number']}"
    return True, ""
