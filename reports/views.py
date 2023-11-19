from collections import defaultdict

from django.db.models import Avg, Count, Max, Min, Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import authentication.constants as PERMISSIONS
from assets.models import Asset
from authentication.mixins import CheckPermissionsMixin
from core.utils import check_permission, convert_date_to_datetime, convert_qp_dict_to_qp
from essentials.models import OpeningSaleData, Product
from expenses.models import ExpenseDetail
from ledgers.models import Ledger
from transactions.choices import TransactionSerialTypes
from transactions.models import Transaction, TransactionDetail


class BalanceSheet(CheckPermissionsMixin, APIView):
    """Balance sheet with date"""

    permissions = [PERMISSIONS.CAN_VIEW_BALANCE_SHEET]

    def get(self, request):
        branch = request.branch
        date = convert_date_to_datetime(request.query_params.get("date"))
        date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        pay_recv = Ledger.get_account_payable_receivable(branch, date)
        account_balances = Ledger.get_total_account_balance(branch, date, True)

        revenue = TransactionDetail.calculate_total_revenue(branch, None, date)
        cogs = TransactionDetail.calculate_cogs(branch, None, date)
        inventory = TransactionDetail.calculate_previous_inventory(branch, date, True)
        gross_profit = revenue - cogs

        return Response(
            {
                "assets": {
                    "receivable": pay_recv["receivable"],
                    "inventory": inventory,
                    "cash_and_equivalent": account_balances["credit"]
                    - account_balances["debit"],
                    "assets": Asset.get_total_assets(branch, date),
                },
                "liabilities": {
                    "payable": pay_recv["payable"],
                },
                "equity": {
                    "equity": Ledger.get_total_owners_equity(branch, date)
                    + gross_profit
                    + Asset.get_total_asset_profit(branch, date)
                    + OpeningSaleData.get_opening_profit(branch, date)
                    - ExpenseDetail.calculate_total_expenses(branch, None, date),
                },
                "date": date,
            },
            200,
        )


class IncomeStatement(CheckPermissionsMixin, APIView):
    """Income statement with start and end date"""

    permissions = [PERMISSIONS.CAN_VIEW_INCOME_STATEMENT]

    def get(self, request):
        branch = request.branch

        date__gte = convert_date_to_datetime(
            request.query_params.get("date__gte"), True
        )
        if date__gte:
            date__gte = date__gte.replace(
                hour=00, minute=00, second=00, microsecond=000000
            )

        date__lte = convert_date_to_datetime(request.query_params.get("date__lte"))
        date__lte = date__lte.replace(hour=23, minute=59, second=59, microsecond=999999)

        revenue = TransactionDetail.calculate_total_revenue(
            branch, date__gte, date__lte
        )

        opening_sale_data = OpeningSaleData.get_opening_sales_data(branch, date__lte)
        expenses = list(
            ExpenseDetail.calculate_total_expenses_with_expense_head(
                branch, date__gte, date__lte
            )
        )
        expenses.append(
            {"expense__type": "Opening Expense", "total": opening_sale_data["expenses"]}
        )
        final_data = {
            "revenue": revenue + (opening_sale_data["revenue"] or 0),
            "cogs": TransactionDetail.calculate_cogs(branch, date__gte, date__lte)
            + (opening_sale_data["cogs"] or 0),
            "expenses": expenses,
            "asset_profit": Asset.get_total_asset_profit(branch, date__lte, date__gte),
            "date__gte": date__gte,
            "date__lte": date__lte,
        }

        return Response(final_data, status=status.HTTP_200_OK)


class GetAllBalances(CheckPermissionsMixin, APIView):
    """
    Get balances with filters
    """

    permissions = {
        "or": [
            PERMISSIONS.CAN_VIEW_PARTIAL_BALANCES,
            PERMISSIONS.CAN_VIEW_FULL_BALANCES,
        ]
    }

    def get(self, request):
        filters = {"person__branch": request.branch}

        if request.query_params.get("person_type"):
            filters.update(
                {"person__person_type": request.query_params.get("person_type")}
            )
        if request.query_params.get("person_id"):
            filters.update({"person": request.query_params.get("person_id")})
        if request.query_params.get("date__lte"):
            filters.update({"date__lte": request.query_params.get("date__lte")})
        if not check_permission(request, PERMISSIONS.CAN_VIEW_FULL_BALANCES):
            filters.update({"person__person_type": "C"})

        balances = (
            Ledger.objects.filter(**filters)
            .values("nature", "person")
            .order_by("nature")
            .annotate(balance=Sum("amount"))
        )

        data = defaultdict(float)
        for b in balances:
            name = str(b["person"])
            amount = b["balance"]
            nature = b["nature"]
            if nature == "C":
                data[name] = data[name] + amount
            else:
                data[name] = data[name] - amount

        balance_gte = request.query_params.get("balance__gte")
        balance_lte = request.query_params.get("balance__lte")
        balance_nature = request.query_params.get("balance_nature")

        if balance_gte or balance_lte:
            if not balance_nature:
                return Response(
                    {"error": "Please choose a balance nature"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            final_balances = {}
            if balance_gte:
                target_balance = float(balance_gte)
                for person, balance in data.items():
                    curr_balance = abs(balance) if balance_nature == "D" else balance
                    if curr_balance >= target_balance:
                        final_balances[person] = balance
            if balance_lte:
                target_balance = float(balance_lte)
                for person, balance in data.items():
                    curr_balance = abs(balance) if balance_nature == "D" else balance
                    if curr_balance <= target_balance:
                        final_balances[person] = balance

            return Response(final_balances, status=status.HTTP_200_OK)
        elif balance_nature:
            final_balances = {}
            for person, balance in data.items():
                if balance_nature == "C":
                    if balance >= 0.0:
                        final_balances[person] = balance
                else:
                    if balance < 0.0:
                        final_balances[person] = balance
            return Response(final_balances, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_200_OK)


class GetLowStock(CheckPermissionsMixin, APIView):
    """Low stock with product category and warehouse filter"""

    permissions = [PERMISSIONS.CAN_VIEW_LOW_STOCK]

    def get(self, request, *args, **kwargs):
        branch = request.branch
        category_filter = {}
        is_gazaana_ignored = False
        treshold = request.query_params.get("treshold", 0)
        if request.query_params.get("category"):
            category_filter = {"category": request.query_params.get("category")}

        products = Product.objects.filter(**category_filter)
        all_stock = Transaction.get_all_stock(branch, None)
        # all_stock = list(filter(lambda x: x["quantity"] <= float(treshold), all_stock))
        if request.query_params.get("warehouse"):
            all_stock = list(
                filter(
                    lambda x: str(x["warehouse"])
                    == str(request.query_params.get("warehouse")),
                    all_stock,
                )
            )

        filtered_all_stock = (
            []
        )  # only those products' stock that are in Product queryset
        for p in products:
            stock_prod = list(
                filter(lambda x: str(x["product"]) == str(p.id), all_stock)
            )
            if len(stock_prod):
                filtered_all_stock.extend(stock_prod)

        additional_stock = []
        for p in products:
            if not any(s["product"] == str(p.id) for s in all_stock):
                additional_stock.append({"product": p.id})

        if request.query_params.get("ignoreGazaana"):
            is_gazaana_ignored = True
            combined_gazaana_stock = defaultdict(float)
            for f in filtered_all_stock:
                key = f["product"] + "|" + f["warehouse"]
                combined_gazaana_stock[key] = (
                    combined_gazaana_stock[key] + f["quantity"]
                )

            new_combined_stock = []
            for key, value in combined_gazaana_stock.items():
                [product, warehouse] = key.split("|")
                new_combined_stock.append(
                    {"product": product, "warehouse": warehouse, "quantity": value}
                )

            filtered_all_stock = new_combined_stock

        if request.query_params.get("ignoreWarehouse"):
            combined_warehouse_stock = defaultdict(float)
            if not is_gazaana_ignored:
                for f in filtered_all_stock:
                    key = f"{f['product']}|{f['yards_per_piece']}"
                    combined_warehouse_stock[key] = (
                        combined_warehouse_stock[key] + f["quantity"]
                    )
                new_combined_stock = []
                for key, value in combined_warehouse_stock.items():
                    [product, yards_per_piece] = key.split("|")
                    new_combined_stock.append(
                        {
                            "product": product,
                            "yards_per_piece": yards_per_piece,
                            "quantity": value,
                        }
                    )
            else:
                for f in filtered_all_stock:
                    key = f["product"]
                    combined_warehouse_stock[key] = (
                        combined_warehouse_stock[key] + f["quantity"]
                    )

                new_combined_stock = []
                for key, value in combined_warehouse_stock.items():
                    new_combined_stock.append({"product": key, "quantity": value})

            filtered_all_stock = new_combined_stock

        # now check the treshold of the filtered products
        all_stock = list(
            filter(lambda x: x["quantity"] <= float(treshold), filtered_all_stock)
        )

        return Response([*all_stock, *additional_stock], status=status.HTTP_200_OK)


class ProductPerformanceHistory(CheckPermissionsMixin, APIView):
    """
    statistics for a particular product or all products
    optional customer selected for customer purchase history
    """

    permissions = [PERMISSIONS.CAN_VIEW_PRODUCT_PERFORMANCE]

    def get(self, request):
        filters = {
            "transaction__person__branch": request.branch,
            # "transaction__serial_type": TransactionSerialTypes.INV,
        }
        values = ["product__name", "transaction__serial_type", "yards_per_piece"]
        person = request.query_params.get("person")
        product = request.query_params.get("product")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        category = request.query_params.get("category")
        gazaana = request.query_params.get("gazaana")
        if person:
            filters.update({"transaction__person": person})
            values.append("transaction__person")
        if product:
            filters.update({"product": product})
        if start:
            filters.update({"transaction__date__gte": start})
        if end:
            filters.update({"transaction__date__lte": end})
        if category:
            filters.update({"product__category": category})
        if gazaana:
            filters.update({"yards_per_piece": gazaana})

        stats = (
            TransactionDetail.objects.values(*values)
            .annotate(
                quantity_sold=Sum("quantity"),
                average_rate=Avg("rate"),
                minimum_rate=Min("rate"),
                maximum_rate=Max("rate"),
                number_of_times_sold=Count("transaction__id"),
            )
            .filter(**filters)
            .order_by("-quantity_sold")
        )

        qty_sold = defaultdict(float)
        num_invoices = defaultdict(float)
        for s in stats:
            key = f"{s['product__name']}|{s['yards_per_piece']}"
            if s["transaction__serial_type"] == TransactionSerialTypes.INV:
                qty_sold[key] += s["quantity_sold"]
                num_invoices[key] += s["number_of_times_sold"]
            elif s["transaction__serial_type"] == TransactionSerialTypes.MWC:
                qty_sold[key] -= s["quantity_sold"]
                num_invoices[key] -= s["number_of_times_sold"]

        invoices_only_stats = list(
            filter(
                lambda x: x["transaction__serial_type"] == TransactionSerialTypes.INV,
                stats,
            )
        )

        final_stats = map(
            lambda x: {
                **x,
                "quantity_sold": qty_sold[
                    f"{x['product__name']}|{x['yards_per_piece']}"
                ],
                "number_of_times_sold": num_invoices[
                    f"{x['product__name']}|{x['yards_per_piece']}"
                ],
            },
            invoices_only_stats,
        )

        return Response(
            sorted(final_stats, key=lambda x: x["quantity_sold"], reverse=True),
            status=status.HTTP_200_OK,
        )


class RevenueByPeriod(CheckPermissionsMixin, APIView):
    permissions = [PERMISSIONS.CAN_VIEW_REVENUE_BY_PERIOD]

    def get(self, request):
        qpDict = dict(request.GET.lists())
        qps = convert_qp_dict_to_qp(qpDict)
        start = qps.pop("start", None)
        end = qps.pop("end", None)
        period = qps.pop("period", "day")
        serial_type = qps.pop("serial_type", None)

        data = TransactionDetail.calculate_revenue_of_period(
            request.branch, period, start, end, serial_type=serial_type
        )

        return Response(
            {
                "revenue": data["revenue"],
                "discounts": data["discounts"],
                "period": period,
            },
            status=status.HTTP_200_OK,
        )
