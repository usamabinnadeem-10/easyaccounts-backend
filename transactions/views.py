from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import *

from .models import Transaction
from .serializers import TransactionSerializer

import datetime


class CreateTransaction(
    generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView
):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def list(self, request, *args, **kwargs):
        try:
            person = request.data["person"]
            startDate = request.data["start"] or timezone.now()
            endDate = request.data["end"] or timezone.now()
            transactions = Transaction.objects.filter(
                date__gte=startDate, date__lte=endDate, person=person
            )
            serialized = TransactionSerializer(transactions, many=True)
            return Response(serialized.data)
        except ValueError:
            return Response(ValueError, status=HTTP_400_BAD_REQUEST)
