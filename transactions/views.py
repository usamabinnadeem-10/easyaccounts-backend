from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.views import APIView
from rest_framework.exceptions import NotAcceptable

from ledgers.models import Ledger

from essentials.serializers import AccountTypeSerializer
from .models import Transaction, TransactionDetail
from .serializers import (
    TransactionSerializer,
    UpdateTransactionSerializer,
)

from django.db.models import Min, Sum
from datetime import date


class GetOrCreateTransaction(generics.ListCreateAPIView):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def list(self, request, *args, **kwargs):
        transactions = self.get_queryset()
        try:
            qp = request.query_params
            person = qp.get("person")
            startDate = (
                qp.get("start")
                or transactions.aggregate(Min("date"))["date__min"]
                or date.today()
            )
            endDate = qp.get("end") or date.today()
            transactions = transactions.filter(
                date__gte=startDate, date__lte=endDate, person=person, draft=False
            )
            serialized_transaction = TransactionSerializer(transactions, many=True).data
            final_data = []
            all_ledgers = Ledger.objects.all()
            for transaction in serialized_transaction:
                paid_amount = None
                serialized_account_type = None
                ledger_instance = all_ledgers.filter(
                    transaction=transaction["id"], account_type__isnull=False
                )
                if len(ledger_instance):
                    serialized_account_type = (
                        AccountTypeSerializer(ledger_instance[0].account_type).data
                        if ledger_instance[0].account_type
                        else None
                    )
                    paid_amount = ledger_instance[0].amount
                final_data.append(
                    {
                        "transaction": transaction,
                        "account_type": serialized_account_type,
                        "paid_amount": paid_amount,
                    }
                )

            return Response(final_data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(ValueError, status=HTTP_400_BAD_REQUEST)


class EditUpdateDeleteTransaction(generics.RetrieveUpdateDestroyAPIView):

    queryset = Transaction.objects.all()
    serializer_class = UpdateTransactionSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ledger_instance = Ledger.objects.filter(
            transaction=instance, account_type__isnull=False
        )
        serialized_transaction = TransactionSerializer(instance).data
        serialized_account_type = None
        paid_amount = None
        if len(ledger_instance):
            serialized_account_type = (
                AccountTypeSerializer(ledger_instance[0].account_type).data
                if ledger_instance[0].account_type
                else None
            )
            paid_amount = ledger_instance[0].amount
        return Response(
            {
                "transaction": serialized_transaction,
                "account_type": serialized_account_type,
                "paid_amount": paid_amount,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class GetProductQuantity(APIView):
    def get(self, request):
        try:
            product = request.query_params.get("product")
            startDate = (
                request.query_params.get("start")
                or Transaction.objects.all().aggregate(Min("date"))["date__min"]
            )
            endDate = request.query_params.get("end") or date.today()
            if product:
                warehouse = request.query_params.get("warehouse")
                transaction_query = {
                    "date__gte": startDate,
                    "date__lte": endDate,
                    "nature": "C",
                    "draft": False,
                }
                credits = Transaction.objects.filter(**transaction_query)
                detail_query = {
                    "transaction__in": credits,
                    "product": product,
                }
                if warehouse:
                    detail_query["warehouse"] = warehouse

                credit_details = TransactionDetail.objects.filter(**detail_query)

                transaction_query["nature"] = "D"
                debits = Transaction.objects.filter(**transaction_query)
                detail_query["transaction__in"] = debits
                debit_details = TransactionDetail.objects.filter(**detail_query)

                quantity_in = 0.0
                quantity_out = 0.0
                for c in credit_details:
                    quantity_in += c.quantity

                for d in debit_details:
                    quantity_out += d.quantity

                return Response(
                    {
                        "quantity": quantity_in - quantity_out,
                        "quantity_in": quantity_in,
                        "quantity_out": quantity_out,
                    },
                    status=status.HTTP_200_OK,
                )
            raise NotAcceptable
        except KeyError:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class GetAllQuantity(APIView):
    def get(self, request):
        transactions = (
            TransactionDetail.objects.values_list("product", "transaction__nature")
            .filter(transaction__draft=False)
            .annotate(Sum("quantity"))
        )

        data = {}

        for transaction in transactions:
            current_product = str(transaction[0])
            if not current_product in data:
                data[current_product] = {
                    transaction[1]: transaction[2],
                }
            else:
                new = data[current_product]
                new[transaction[1]] = transaction[2]

        return Response(transactions, status=HTTP_200_OK)
