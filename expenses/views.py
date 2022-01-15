from rest_framework import generics

from django_filters.rest_framework import DjangoFilterBackend

from .models import ExpenseAccount, ExpenseDetail
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer


class CreateExpenseAccount(generics.ListCreateAPIView):
    """
    create expense account or list all expense accounts
    """
    queryset = ExpenseAccount.objects.all()
    serializer_class = ExpenseAccountSerializer


class CreateExpenseDetail(generics.ListCreateAPIView):
    """
    get expense details with optional filters
    """
    serializer_class = ExpenseDetailSerializer
    queryset = ExpenseDetail.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        'date': ['gte', 'lte'],
        'amount': ['gte', 'lte'],
        'account_type': ['exact'],
        'detail': ['icontains'],
    }


class EditUpdateDeleteExpenseDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Edit / Update / Delete an expense record
    """
    queryset = ExpenseDetail.objects.all()
    serializer_class = ExpenseDetailSerializer
