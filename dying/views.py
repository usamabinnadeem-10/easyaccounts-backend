from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.
from rest_framework import generics

from .queries import DyingIssueQuery, DyingUnitQuery
from .serializers import (
    DyingIssueSerializer,
    DyingUnitSerializer,
    IssueForDyingSerializer,
)


class CreateDyingUnit(DyingUnitQuery, generics.CreateAPIView):

    serializer_class = DyingUnitSerializer


class ListDyingUnit(DyingUnitQuery, generics.ListAPIView):

    serializer_class = DyingUnitSerializer


class ListIssuedLotsView(DyingIssueQuery, generics.ListAPIView):

    serializer_class = DyingIssueSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte", "exact"],
        "dying_lot_number": ["gte", "lte", "exact"],
        "dying_unit": ["exact"],
        "dying_issue_lot__lot_number": ["gte", "lte", "exact"],
    }


class IssueForDyingView(DyingIssueQuery, generics.CreateAPIView):

    serializer_class = IssueForDyingSerializer
