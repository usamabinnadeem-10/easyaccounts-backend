from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from essentials.models import Person

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from datetime import date, timedelta, datetime
from django.db.models import Min, Sum, F


class CreateOrListLedgerDetail(generics.ListCreateAPIView):
    queryset = Ledger.objects.select_related("person", "account_type", "transaction")
    serializer_class = LedgerSerializer

    def list(self, request, *args, **kwargs):
        ledgers = self.queryset
        qp = request.query_params
        person = qp.get("person")
        start = (
            datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
        )
        startDate = (
            start
            or ledgers.filter(person=person).aggregate(Min("date"))["date__min"]
            or date.today()
        )
        startDateMinusOne = startDate - timedelta(days=1)
        endDate = qp.get("end") or date.today()

        if person:
            previous_queryset = ledgers.filter(
                person=person, date__lte=startDateMinusOne, draft=False
            )
            opening_balance = 0.0
            for prev in previous_queryset:
                if prev.nature == "D":
                    opening_balance -= prev.amount
                else:
                    opening_balance += prev.amount

            queryset = ledgers.filter(
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


class GetAllBalances(APIView):
    def get(self, request):
        person_type = request.query_params.get("person")

        test = (
            Ledger.objects.values("nature", name=F("person__name"))
            .annotate(balance=Sum("amount"))
            .filter(person__person_type=person_type)
        )

        return Response(test, status=status.HTTP_200_OK)
