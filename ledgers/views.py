from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Min, Sum, F

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from essentials.pagination import CustomPagination

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from datetime import date, datetime, timedelta


class CreateOrListLedgerDetail(generics.ListCreateAPIView):
    """
    get ledger of a person by start date, end date, (when passing neither all ledger is returned)
    returns paginated response along with opening balance
    """
    serializer_class = LedgerSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method == "POST":
            return Ledger.objects.all()
        elif self.request.method == "GET":
            qp = self.request.query_params
            person = qp.get("person")
            endDate = qp.get("end") or date.today()
            return Ledger.objects.select_related(
                "person", "account_type", "transaction"
            ).filter(person=person, date__lte=endDate, draft=False)

    def list(self, request, *args, **kwargs):
        qp = self.request.query_params
        queryset = self.get_queryset()

        startDate = (
            (datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None) 
            or (queryset.aggregate(Min("date"))["date__min"] or date.today())
        )
        startDateMinusOne = startDate - timedelta(days=1)
        balance =  queryset.values("nature") \
            .order_by("nature") \
            .annotate(amount=Sum("amount")) \
            .filter(date__lte=startDateMinusOne)
        
        opening_balance = 0
        for b in balance:
            opening_balance += b["amount"] if b["nature"] == "C" else -b["amount"]
        
        ledger_data = LedgerSerializer(
            self.paginate_queryset(
                queryset.filter(date__gte=startDate).order_by('-date','-transaction__serial')
                ), many=True).data
        page = self.get_paginated_response(ledger_data)
        page.data['opening_balance'] = opening_balance
        

        return Response(page.data, status=status.HTTP_200_OK)


class EditUpdateDeleteLedgerDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Edit / Update / Delete a ledger record
    """
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer



class GetAllBalances(APIView):
    """
    Get all balances
    Expects a query parameter person (S or C)
    """
    def get(self, request):
        person_type = request.query_params.get("person")

        balances = (
            Ledger.objects.values("nature", name=F("person__name"))
            .order_by("nature")
            .annotate(balance=Sum("amount"))
            .filter(person__person_type=person_type)
        )

        return Response(balances, status=status.HTTP_200_OK)


class FilterLedger(generics.ListAPIView):
    """
    filter ledger records
    """
    serializer_class = LedgerSerializer
    queryset = Ledger.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        'date': ['gte', 'lte'],
        'amount': ['gte', 'lte'],
        'account_type': ['exact'],
        'detail': ['contains'],
        'nature': ['exact'],
        'person': ['exact'],
    }