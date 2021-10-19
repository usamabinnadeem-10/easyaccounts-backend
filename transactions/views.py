from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import *

from .models import Transaction
from .serializers import TransactionSerializer

from datetime import date


class CreateTransaction(
    generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView
):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def list(self, request, *args, **kwargs):
        try:
            qp = request.query_params
            person = qp.get("person")
            startDate = qp.get("start") or date.today()
            endDate = qp.get("end") or date.today()
            transactions = Transaction.objects.filter(
                date__gte=startDate, date__lte=endDate, person=person
            )
            serialized = TransactionSerializer(transactions, many=True)
            return Response(serialized.data)
        except ValueError:
            return Response(ValueError, status=HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
