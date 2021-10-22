from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.views import APIView
from rest_framework.exceptions import NotAcceptable

from .models import Transaction, TransactionDetail
from .serializers import TransactionSerializer

from django.db.models import Min
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
            startDate = (
                qp.get("start")
                or Transaction.objects.all().aggregate(Min("date"))["date__min"]
            )
            endDate = qp.get("end") or date.today()
            transactions = Transaction.objects.filter(
                date__gte=startDate, date__lte=endDate, person=person, draft=False
            )
            serialized = TransactionSerializer(transactions, many=True)
            return Response(serialized.data)
        except ValueError:
            return Response(ValueError, status=HTTP_400_BAD_REQUEST)


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

                quantity = 0.0
                for c in credit_details:
                    quantity += c.quantity

                for d in debit_details:
                    quantity -= d.quantity

                return Response({"quantity": quantity}, status=status.HTTP_200_OK)
            raise NotAcceptable
        except KeyError:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
