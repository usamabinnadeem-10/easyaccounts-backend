from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer


class LedgerDetail(
    generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView
):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
    lookup_field = "id"

    def list(self, request, *args, **kwargs):
        person = self.request.query_params.get("person")
        if person:
            queryset = Ledger.objects.filter(person=person)
            serialized = LedgerSerializer(queryset, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
