from collections import defaultdict

from django.db.models import F, Sum
from dying.models import DyingIssueDetail

from .models import RawPurchaseLotDetail, RawSaleAndReturnLotDetail


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
            RawPurchaseLotDetail.objects.values(
                "purchase_lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "warehouse",
                "formula",
                raw_product=F("purchase_lot_number__raw_product"),
            )
            .filter(
                purchase_lot_number__raw_product__person__branch=branch,
                purchase_lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_lots = list(
        map(
            lambda obj: {
                **obj,
                "nature": "C",
                # "raw_product": obj["lot_number__raw_product"],
            },
            balance_lots,
        )
    )

    balance_returns = list(
        (
            RawSaleAndReturnLotDetail.objects.values(
                "actual_gazaana",
                "expected_gazaana",
                "warehouse",
                "formula",
                "nature",
                lot_number=F("sale_and_return_id__purchase_lot_number"),
                raw_product=F("sale_and_return_id__purchase_lot_number__raw_product"),
            )
            .filter(
                # sale_and_return_id__purchase_lot_number__raw_product__person__branch=branch,
                # sale_and_return_id__purchase_lot_number__issued=False,
                sale_and_return_id__purchase_lot_number__raw_product__person__branch=branch,
                sale_and_return_id__purchase_lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_returns = list(
        map(
            lambda obj: {
                **obj,
                # "lot_number": obj["return_lot__lot_number"],
                # "raw_product": obj["return_lot__lot_number__raw_product"],
            },
            balance_returns,
        )
    )

    balance_dyings = list(
        (
            DyingIssueDetail.objects.values(
                "actual_gazaana",
                "expected_gazaana",
                "formula",
                "warehouse",
                lot_number=F("dying_lot_number__purchase_lot_number"),
                raw_product=F("dying_lot_number__purchase_lot_number__raw_product"),
            )
            .filter(
                # dying_lot_number__dying_lot__dying_unit__branch=branch,
                # dying_lot_number__lot_number__issued=False,
                dying_lot_number__purchase_lot_number__issued=False,
                formula__branch=branch,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_dyings = list(
        map(
            lambda obj: {
                **obj,
                "nature": "D",
                # "raw_product": obj["dying_lot_number__lot_number__raw_product"],
                # "lot_number": obj["dying_lot_number__lot_number"],
            },
            balance_dyings,
        )
    )

    return [*balance_lots, *balance_returns, *balance_dyings]
