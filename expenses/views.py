from rest_framework import generics

from django_filters.rest_framework import DjangoFilterBackend

from .models import ExpenseAccount, ExpenseDetail
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer
from .filters import DateFilter



class CreateExpenseAccount(generics.ListCreateAPIView):
    """
    create expense account or list all expense accounts
    """
    queryset = ExpenseAccount.objects.all()
    serializer_class = ExpenseAccountSerializer


class CreateExpenseDetail(generics.ListCreateAPIView):
    """
    get expense details with optional filters such as account type, start or end date
    """
    serializer_class = ExpenseDetailSerializer
    queryset = ExpenseDetail.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['account_type']



class EditUpdateDeleteExpenseDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Edit / Update / Delete an expense record
    """
    queryset = ExpenseDetail.objects.all()
    serializer_class = ExpenseDetailSerializer
