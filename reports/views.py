from assets.models import Asset
from core.utils import convert_date_to_datetime
from django.db.models import Avg, Count, Sum
from essentials.models import OpeningSaleData
from expenses.models import ExpenseDetail
from ledgers.models import Ledger
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from transactions.models import TransactionDetail


class BalanceSheet(APIView):
    """Balance sheet with date"""

    def get(self, request):
        branch = request.branch
        date = convert_date_to_datetime(request.query_params.get("date"))
        date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        pay_recv = Ledger.get_account_payable_receivable(branch, date)
        account_balances = Ledger.get_total_account_balance(branch, date, True)
        transaction_stats = TransactionDetail.get_inventory_stats(branch, date)
        return Response(
            {
                "assets": {
                    "receivable": pay_recv["receivable"],
                    "inventory": transaction_stats["inventory"],
                    "cash_in_hand": account_balances["credit"]
                    - account_balances["debit"],
                    "total_assets": Asset.get_total_assets(branch, date),
                },
                "liabilities": {
                    "payable": pay_recv["payable"],
                },
                "equity": {
                    "equity": Ledger.get_total_owners_equity(branch, date)
                    + transaction_stats["profit"]
                    + Asset.get_total_asset_profit(branch, date)
                    + OpeningSaleData.get_opening_profit(branch, date)
                    - ExpenseDetail.calculate_total_expenses(branch, None, date),
                },
            },
            200,
        )


class IncomeStatement(APIView):
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
        inventory_stats = TransactionDetail.get_inventory_stats(
            branch, date__lte, date__gte
        )
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
            "cogs": (revenue - inventory_stats["profit"])
            + (opening_sale_data["cogs"] or 0),
            "expenses": expenses,
            "asset_profit": Asset.get_total_asset_profit(branch, date__lte, date__gte),
        }

        return Response(final_data, status=status.HTTP_200_OK)
