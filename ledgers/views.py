from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from essentials.pagination import CustomPagination

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from datetime import date, datetime, timedelta
from django.db.models import Min, Sum, F


class CreateOrListLedgerDetail(generics.ListCreateAPIView):
    serializer_class = LedgerSerializer
    pagination_class = CustomPagination

    # def get_queryset(self):
    #     qp = self.request.query_params
    #     person = qp.get("person")
    #     endDate = qp.get("end") or date.today()
    #     queryset = Ledger.objects.select_related(
    #         "person", "account_type", "transaction"
    #     ).filter(person=person, date__lte=endDate, draft=False)

    #     start = (
    #         datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
    #     )

    #     startDate = (
    #         start or queryset.aggregate(Min("date"))["date__min"] or date.today()
    #     )

    #     startDateMinusOne = startDate - timedelta(days=1)
    #     balance = list(
    #         queryset.filter(date__lte=startDateMinusOne)
    #         .values("nature")
    #         .annotate(amount=Sum("amount"))
    #     )
    #     opening_balance = 0
    #     for b in balance:
    #         opening_balance = (
    #             opening_balance + b["amount"] if b["nature"] == "C" else -b["amount"]
    #         )

    #     return {
    #         'ledger_data': queryset.filter(date__gte=startDate),
    #         'opening_balance': opening_balance,
    #     }

    def list(self, request, *args, **kwargs):
        qp = self.request.query_params
        person = qp.get("person")
        endDate = qp.get("end") or date.today()
        queryset = Ledger.objects.select_related(
            "person", "account_type", "transaction"
        ).filter(person=person, date__lte=endDate, draft=False)

        start = (
            datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
        )

        startDate = (
            start or queryset.aggregate(Min("date"))["date__min"] or date.today()
        )

        startDateMinusOne = startDate - timedelta(days=1)
        balance = list(
            queryset.filter(date__lte=startDateMinusOne)
            .values("nature")
            .annotate(amount=Sum("amount"))
        )
        opening_balance = 0
        for b in balance:
            opening_balance = (
                opening_balance + b["amount"] if b["nature"] == "C" else -b["amount"]
            )
        ledger_data = LedgerSerializer(queryset.filter(date__gte=startDate), many=True).data
        page = self.paginate_queryset(ledger_data)
        print(page)
        page = self.get_paginated_response(page)
        
        return page
        return Response({
            'ledger': page,
            'opening_balance': opening_balance,
        }, status=status.HTTP_200_OK)


class EditUpdateDeleteLedgerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer


class GetAllBalances(APIView):
    def get(self, request):
        person_type = request.query_params.get("person")

        test = (
            Ledger.objects.values("nature", name=F("person__name"))
            .annotate(balance=Sum("amount"))
            .filter(person__person_type=person_type)
        )

        return Response(test, status=status.HTTP_200_OK)
