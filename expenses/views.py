from rest_framework import generics
from .models import ExpenseAccount, ExpenseDetail
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer


class CreateExpenseAccount(generics.ListCreateAPIView):

    queryset = ExpenseAccount.objects.all()
    serializer_class = ExpenseAccountSerializer


class CreateExpenseDetail(generics.ListCreateAPIView):

    queryset = ExpenseDetail.objects.all()
    serializer_class = ExpenseDetailSerializer


class EditUpdateDeleteExpenseDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = ExpenseDetail.objects.all()
    serializer_class = ExpenseDetailSerializer
