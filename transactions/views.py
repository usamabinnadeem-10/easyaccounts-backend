from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import *


from essentials.pagination import CustomPagination
from .models import Transaction, TransactionDetail
from .serializers import (
    TransactionSerializer,
    UpdateTransactionSerializer,
    update_stock,
)

from django.db.models import Min, Max, Avg, Sum, Count
from datetime import date


class GetOrCreateTransaction(generics.ListCreateAPIView):
    """
    get transactions with a time frame (optional), requires person to be passed
    """

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
    """
    Edit / Update / Delete a transaction
    """

    queryset = Transaction.objects.all()
    serializer_class = UpdateTransactionSerializer

    def delete(self, *args, **kwargs):
        instance = self.get_object()

        transaction_details = TransactionDetail.objects.filter(
            transaction=instance
        ).values(
            "product",
            "quantity",
            "warehouse",
            "yards_per_piece",
        )

        for transaction in transaction_details:
            update_stock("C" if instance.nature == "D" else "D", transaction)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FilterTransactions(generics.ListAPIView):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "account_type": ["exact"],
        "detail": ["icontains"],
        "person": ["exact"],
        "draft": ["exact"],
        "serial": ["exact", "gte", "lte"],
        "discount": ["gte", "lte"],
        "type": ["exact"],
        "transaction_detail__amount": ["gte", "lte"],
    }


class ProductPerformanceHistory(APIView):
    """
    statistics for a particular product or all products
    optional customer selected for customer purchase history
    """

    def get(self, request):
        filters = {"transaction__nature": "D", "transaction__person__person_type": "C"}
        values = ["product__name"]
        person = request.query_params.get("person")
        if person:
            filters.update({"transaction__person": person})
            values.append("transaction__person")
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
            .order_by("-number_of_times_sold", "quantity_sold")
        )

        return Response(stats, status=status.HTTP_200_OK)
