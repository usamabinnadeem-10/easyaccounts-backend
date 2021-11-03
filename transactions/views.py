from typing import final
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.views import APIView
from rest_framework.exceptions import NotAcceptable
from essentials.models import Product

from ledgers.models import Ledger

from essentials.serializers import AccountTypeSerializer
from .models import Transaction, TransactionDetail
from .serializers import TransactionSerializer, UpdateTransactionSerializer

from django.db.models import Min
from datetime import date


class GetOrCreateTransaction(generics.ListCreateAPIView):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def list(self, request, *args, **kwargs):
        try:
            qp = request.query_params
            person = qp.get("person")
            startDate = (
                qp.get("start")
                or Transaction.objects.all().aggregate(Min("date"))["date__min"]
                or date.today()
            )
            endDate = qp.get("end") or date.today()
            transactions = Transaction.objects.filter(
                date__gte=startDate, date__lte=endDate, person=person, draft=False
            )
            serialized_transaction = TransactionSerializer(transactions, many=True).data
            final_data = []
            for transaction in serialized_transaction:
                paid_amount = None
                serialized_account_type = None
                ledger_instance = Ledger.objects.filter(
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


class GetAllProductQuantities(APIView):
    def get(self, request):
        products = Product.objects.all()
        quantity_data = []
        for product in products:
            credits = Transaction.objects.filter(nature="C", draft=False)
            credit_details = TransactionDetail.objects.filter(
                transaction__in=credits, product=product
            )
            debits = Transaction.objects.filter(nature="D", draft=False)
            debit_details = TransactionDetail.objects.filter(
                transaction__in=debits, product=product
            )

            quantity_in = 0.0
            quantity_out = 0.0
            for c in credit_details:
                quantity_in += c.quantity

            for d in debit_details:
                quantity_out += d.quantity

            quantity_data.append(
                {
                    "quantity": quantity_in - quantity_out,
                    "quantity_in": quantity_in,
                    "quantity_out": quantity_out,
                    "product": f"{product.product_head.head_name} {product.product_color.color_name}",
                }
            )

        return Response(quantity_data, status=status.HTTP_200_OK)
