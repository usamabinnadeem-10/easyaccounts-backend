from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.views import APIView
from rest_framework.exceptions import NotAcceptable

from essentials.pagination import CustomPagination
from .models import Transaction, TransactionDetail
from .serializers import (
    TransactionSerializer,
    UpdateTransactionSerializer,
)

from django.db.models import Min, Sum
from datetime import date


class GetOrCreateTransaction(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        transactions = Transaction.objects.select_related(
            "person", "account_type"
        ).prefetch_related(
            "transaction_detail",
            "transaction_detail__product",
            "transaction_detail__warehouse",
        )
        qp = self.request.query_params
        person = qp.get("person")
        startDate = (
            qp.get("start")
            or transactions.aggregate(Min("date"))["date__min"]
            or date.today()
        )
        endDate = qp.get("end") or date.today()
        queryset = transactions.filter(
            date__gte=startDate, date__lte=endDate, person=person, draft=False
        )
        return queryset


class EditUpdateDeleteTransaction(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = UpdateTransactionSerializer


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


class GetAllQuantityByWarehouse(APIView):
    def get(self, request):
        transactions = (
            TransactionDetail.objects.values(
                "product", "transaction__nature", "warehouse"
            )
            .filter(transaction__draft=False)
            .annotate(Sum("quantity"))
        )

        return Response(transactions, status=HTTP_200_OK)