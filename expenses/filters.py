import django_filters
from django_filters import DateFilter

from .models import ExpenseDetail

class CustomDateFilter(django_filters.FilterSet):
    start_date = DateFilter(field_name='date',lookup_expr=('gt'),) 
    end_date = DateFilter(field_name='date',lookup_expr=('lt'))
    queryset = ExpenseDetail.objects.all()

    class Meta:
        model = ExpenseDetail
        fields = '__all__'