from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from datetime import date, timedelta, datetime
from django.db.models import Min


class CreateOrListLedgerDetail(generics.ListCreateAPIView):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer

    def list(self, request, *args, **kwargs):
        qp = request.query_params
        person = qp.get("person")
        start = (
            datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
        )
        startDate = (
            start
            or Ledger.objects.filter(person=person).aggregate(Min("date"))["date__min"]
            or date.today()
        )
        startDateMinusOne = startDate - timedelta(days=1)
        endDate = qp.get("end") or date.today()

        if person:
            previous_queryset = Ledger.objects.filter(
                person=person, date__lte=startDateMinusOne, draft=False
            )
            opening_balance = 0.0
            for prev in previous_queryset:
                if prev.nature == "D":
                    opening_balance -= prev.amount
                else:
                    opening_balance += prev.amount

            queryset = Ledger.objects.filter(
                person=person, date__gte=startDate, date__lte=endDate, draft=False
            )
            serialized = LedgerSerializer(queryset, many=True)
            return Response(
                {"ledger_data": serialized.data, "opening_balance": opening_balance},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "person is required"}, status=status.HTTP_400_BAD_REQUEST
        )


class EditUpdateDeleteLedgerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
