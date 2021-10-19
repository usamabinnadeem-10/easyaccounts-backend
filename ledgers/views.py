from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from datetime import date
from django.db.models import Min


class LedgerDetail(
    generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView
):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
    lookup_field = "id"

    def list(self, request, *args, **kwargs):
        qp = request.query_params
        person = qp.get("person")
        startDate = (
            qp.get("start")
            or Ledger.objects.filter(person=person).aggregate(Min("date"))["date__min"]
        )
        endDate = qp.get("end") or date.today()

        if person:
            queryset = Ledger.objects.filter(
                person=person, date__gte=startDate, date__lte=endDate
            )
            serialized = LedgerSerializer(queryset, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
