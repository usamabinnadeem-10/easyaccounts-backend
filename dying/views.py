from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend

from .queries import DyingUnitQuery
from .serializers import (
    DyingUnitSerializer,
)


class CreateDyingUnit(DyingUnitQuery, generics.CreateAPIView):

    serializer_class = DyingUnitSerializer


class ListDyingUnit(DyingUnitQuery, generics.ListAPIView):

    serializer_class = DyingUnitSerializer
