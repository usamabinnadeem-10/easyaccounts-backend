from collections import defaultdict

from assets.models import Asset
from authentication.choices import RoleChoices
from authentication.mixins import (
    IsAdminOrReadAdminOrAccountantMixin,
    IsAdminOrReadAdminPermissionMixin,
)
from core.utils import convert_date_to_datetime
from django.db.models import Sum
from essentials.models import OpeningSaleData, Product
from expenses.models import ExpenseDetail
from ledgers.models import Ledger
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from transactions.models import Transaction, TransactionDetail


class BalanceSheet(IsAdminOrReadAdminPermissionMixin, APIView):
    """Balance sheet with date"""

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


class IncomeStatement(IsAdminOrReadAdminPermissionMixin, APIView):
    """Income statement with start and end date"""

    def get(self, request):
        branch = request.branch

        date__gte = convert_date_to_datetime(request.query_params.get("date__gte"), True)
        if date__gte:
            date__gte = date__gte.replace(
                hour=00, minute=00, second=00, microsecond=000000
            )

        date__lte = convert_date_to_datetime(request.query_params.get("date__lte"))
        date__lte = date__lte.replace(hour=23, minute=59, second=59, microsecond=999999)

        revenue = TransactionDetail.calculate_total_revenue(branch, date__gte, date__lte)

        opening_sale_data = OpeningSaleData.get_opening_sales_data(branch, date__lte)
        expenses = list(
            ExpenseDetail.calculate_total_expenses_with_category(
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


class GetAllBalances(IsAdminOrReadAdminOrAccountantMixin, APIView):
    """
    Get balances with filters
    """

    def get(self, request):
        filters = {"person__branch": request.branch}

        if request.query_params.get("person_type"):
            filters.update(
                {"person__person_type": request.query_params.get("person_type")}
            )
        if request.query_params.get("person_id"):
            filters.update({"person": request.query_params.get("person_id")})

        if request.role not in [RoleChoices.ADMIN, RoleChoices.ADMIN_VIEWER]:
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


class GetLowStock(APIView):
    """Low stock with product category and warehouse filter"""

    def get(self, request, *args, **kwargs):
        branch = request.branch
        category_filter = {}
        treshold = request.query_params.get("treshold", 0)
        if request.query_params.get("category"):
            category_filter = {"category": request.query_params.get("category")}
        products = Product.objects.filter(**category_filter)
        all_stock = Transaction.get_all_stock(branch, None)
        all_stock = list(filter(lambda x: x["quantity"] <= float(treshold), all_stock))
        if request.query_params.get("warehouse"):
            all_stock = list(
                filter(
                    lambda x: x["warehouse"] == request.query_params.get("warehouse"),
                    all_stock,
                )
            )
        # all_stock = {s['product'] for s in all_stock}
        additional_stock = []
        for p in products:
            if not any(s["product"] == str(p.id) for s in all_stock):
                additional_stock.append({"product": p.id})

        final_low_stock = {s["product"] for s in [*all_stock, *additional_stock]}
        return Response(final_low_stock, status=status.HTTP_200_OK)
