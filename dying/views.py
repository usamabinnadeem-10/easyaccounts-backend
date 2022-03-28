from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.
from rest_framework import generics

from .queries import DyingUnitQuery
from .serializers import DyingUnitSerializer


class CreateDyingUnit(DyingUnitQuery, generics.CreateAPIView):

    serializer_class = DyingUnitSerializer


class ListDyingUnit(DyingUnitQuery, generics.ListAPIView):

    serializer_class = DyingUnitSerializer
