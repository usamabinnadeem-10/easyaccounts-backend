from assets.models import Asset
from core.utils import convert_date_to_datetime
from ledgers.models import Ledger
from rest_framework.response import Response
from rest_framework.views import APIView
from transactions.models import TransactionDetail


class BalanceSheet(APIView):
    """get income statement"""

    def get(self, request):
        branch = request.branch
        date = convert_date_to_datetime(request.query_params.get("date"))
        date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        pay_recv = Ledger.get_account_payable_receivable(branch, date)
        account_balances = Ledger.get_total_account_balance(branch, date, True)
        return Response(
            {
                "transaction_stats": TransactionDetail.get_inventory_stats(branch, date),
                "payable": pay_recv["payable"],
                "receivable": pay_recv["receivable"],
                "cash_in_hand": account_balances["credit"] - account_balances["debit"],
                "total_assets": Asset.get_total_assets(branch, date),
                "equity": Ledger.get_total_owners_equity(branch, date),
            },
            200,
        )
