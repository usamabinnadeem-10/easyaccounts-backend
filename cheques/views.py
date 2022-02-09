from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *
from .models import *
from ledgers.models import Ledger


class CreateChequeEntryView(CreateAPIView):

    queryset = Cheque.objects.all()
    serializer_class = CreateChequeEntrySerializer


class CreateChequeHistoryView(CreateAPIView):

    queryset = ChequeHistory.objects.all()
    serializer_class = ChequeHistorySerializer


class CreateChequeHistoryWithChequeView(CreateAPIView):

    queryset = ChequeHistory.objects.all()
    serializer_class = ChequeHistoryWithChequeSerializer


class GetChequeHistory(ListAPIView):

    queryset = Cheque.objects.all()
    serializer_class = ListChequeHistorySerializer
