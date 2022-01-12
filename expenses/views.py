from rest_framework import generics

from django_filters.rest_framework import DjangoFilterBackend

from .models import ExpenseAccount, ExpenseDetail
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer
from .filters import DateFilter


"""
    create expense account or list all expense accounts
"""
class CreateExpenseAccount(generics.ListCreateAPIView):

    queryset = ExpenseAccount.objects.all()
    serializer_class = ExpenseAccountSerializer

"""
    get expense details with optional filters such as account type, start or end date
"""
class CreateExpenseDetail(generics.ListCreateAPIView):

    serializer_class = ExpenseDetailSerializer
    queryset = ExpenseDetail.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['account_type']


"""
    Edit / Update / Delete an expense record
"""
class EditUpdateDeleteExpenseDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = ExpenseDetail.objects.all()
    serializer_class = ExpenseDetailSerializer
