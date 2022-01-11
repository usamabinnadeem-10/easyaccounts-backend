from django.db.models import query
from rest_framework import generics
from .models import ExpenseAccount, ExpenseDetail
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer

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

    def get_queryset(self):
        query_set = ExpenseDetail.objects.all()
        account_type = self.request.query_params.get("account_type")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if account_type:
            query_set = query_set.filter(account_type=account_type)
        if start:
            query_set = query_set.filter(date__gte=start)
        if end:
            query_set = query_set.filter(date__lte=end)
        return query_set

"""
    Edit / Update / Delete an expense record
"""
class EditUpdateDeleteExpenseDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = ExpenseDetail.objects.all()
    serializer_class = ExpenseDetailSerializer
