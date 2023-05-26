from collections import defaultdict

from django.db.models import Sum

from dying.models import DyingIssueDetail

from .models import RawDebitLotDetail, RawLotDetail


def is_array_unique(array, key):
    uniques = defaultdict(lambda: True)
    for obj in array:
        value = uniques[obj[key]]
        if value:
            uniques[obj[key]] = None
        else:
            return False
    return True


def calculate_amount(lot_details):
    amount = 0
    for detail in lot_details:
        amount += (
            detail["quantity"]
            * detail["rate"]
            * detail["actual_gazaana"]
            * (detail["formula"].numerator / detail["formula"].denominator)
        )
    return amount


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

    balance_returns = list(
        (
            RawDebitLotDetail.objects.values(
                "return_lot__lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "return_lot__lot_number__raw_product",
                "warehouse",
                # "formula",
                "nature",
            )
            .filter(
                return_lot__bill_number__branch=branch,
                return_lot__lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_returns = list(
        map(
            lambda obj: {
                **obj,
                "lot_number": obj["return_lot__lot_number"],
                "raw_product": obj["return_lot__lot_number__raw_product"],
            },
            balance_returns,
        )
    )

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
    return [*balance_lots, *balance_returns, *balance_dyings]
