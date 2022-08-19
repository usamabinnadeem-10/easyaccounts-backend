from collections import defaultdict
from operator import itemgetter

from django.db.models import F, Sum
from dying.models import DyingIssueDetail

from .models import (
    RawPurchaseLotDetail,
    RawSaleAndReturnLotDetail,
    RawStockTransferLotDetail,
)


def get_all_raw_stock(branch, return_raw=False):
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
    balance_lots_final = list(
        map(
            lambda obj: {
                **obj,
                "nature": "C",
            },
            balance_lots,
        )
    )

    balance_returns_final = list(
        (
            RawSaleAndReturnLotDetail.objects.values(
                "actual_gazaana",
                "expected_gazaana",
                "warehouse",
                "formula",
                "nature",
                purchase_lot_number=F("sale_and_return_id__purchase_lot_number"),
                raw_product=F("sale_and_return_id__purchase_lot_number__raw_product"),
            )
            .filter(
                sale_and_return_id__purchase_lot_number__raw_product__person__branch=branch,
                sale_and_return_id__purchase_lot_number__issued=False,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )

    balance_dyings = list(
        (
            DyingIssueDetail.objects.values(
                "actual_gazaana",
                "expected_gazaana",
                "formula",
                "warehouse",
                purchase_lot_number=F("dying_lot_number__purchase_lot_number"),
                raw_product=F("dying_lot_number__purchase_lot_number__raw_product"),
            )
            .filter(
                dying_lot_number__purchase_lot_number__issued=False,
                formula__branch=branch,
            )
            .annotate(quantity=Sum("quantity"))
        )
    )
    balance_dyings_final = list(
        map(
            lambda obj: {
                **obj,
                "nature": "D",
            },
            balance_dyings,
        )
    )

    balance_transfers = list(
        RawStockTransferLotDetail.objects.values(
            "actual_gazaana",
            "expected_gazaana",
            "formula",
            "warehouse",
            from_warehouse=F("raw_stock_transfer_id__raw_transfer__from_warehouse"),
            purchase_lot_number=F("raw_stock_transfer_id__purchase_lot_number"),
            raw_product=F("raw_stock_transfer_id__purchase_lot_number__raw_product"),
        )
        .filter(warehouse__branch=branch)
        .annotate(quantity=Sum("quantity"))
    )

    balance_transfers_final = []
    for t in balance_transfers:
        product = {
            "quantity": t["quantity"],
            "actual_gazaana": t["actual_gazaana"],
            "expected_gazaana": t["expected_gazaana"],
            "formula": t["formula"],
            "purchase_lot_number": t["purchase_lot_number"],
            "raw_product": t["raw_product"],
        }
        balance_transfers_final.append(
            {
                **product,
                "warehouse": t["warehouse"],
                "nature": "C",
            }
        )
        balance_transfers_final.append(
            {
                **product,
                "warehouse": t["from_warehouse"],
                "nature": "D",
            }
        )

    stock = [
        *balance_lots_final,
        *balance_returns_final,
        *balance_dyings_final,
        *balance_transfers_final,
    ]

    if return_raw:
        return stock

    d = defaultdict(lambda: defaultdict(int))

    group_keys = [
        "actual_gazaana",
        "expected_gazaana",
        "raw_product",
        "warehouse",
        "formula",
    ]
    sum_keys = ["quantity"]

    for item in stock:
        for key in sum_keys:
            if item["nature"] == "C":
                d[itemgetter(*group_keys)(item)][key] += item[key]
            else:
                d[itemgetter(*group_keys)(item)][key] -= item[key]

    final_stock = [{**dict(zip(group_keys, k)), **v} for k, v in d.items()]
    return final_stock
