from collections import defaultdict

from django.db.models import Sum

from .models import RawLotDetail, RawReturnLotDetail


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
                "formula",
            )
            .filter(branch=branch, lot_number__issued=False)
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_lots = list(map(lambda obj: {**obj, "nature": "C"}, balance_lots))
    balance_returns = list(
        (
            RawReturnLotDetail.objects.values(
                "return_lot__lot_number",
                "actual_gazaana",
                "expected_gazaana",
                "return_lot__lot_number__raw_product",
                "warehouse",
                "formula",
            )
            .filter(branch=branch, return_lot__lot_number__issued=False)
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_returns = list(
        map(
            lambda obj: {
                **obj,
                "nature": "D",
                "lot_number": obj["return_lot__lot_number"],
                "raw_product": obj["return_lot__lot_number__raw_product"],
            },
            balance_returns,
        )
    )
    return [*balance_lots, *balance_returns]
