from django.urls import path

from .views import (
    CreateFormula,
    CreateRawProduct,
    CreateRawTransaction,
    EditUpdateDeleteRawTransactionView,
    FilterRawDebitTransactions,
    FilterRawTransactions,
    FilterRawTransferTransactions,
    ListFormula,
    ListLotNumberAndIdView,
    ListRawProducts,
    RawDebitView,
    TransferRawStockView,
    ViewAllStock,
)

urlpatterns = [
    # -----------------Raw Transaction--------------------- #
    path("transaction/create/", CreateRawTransaction.as_view()),
    path("transaction/list/", FilterRawTransactions.as_view()),
    path("transaction/<uuid:pk>/", EditUpdateDeleteRawTransactionView.as_view()),
    # -----------------Raw Debit--------------------------- #
    path("transaction/debit/", RawDebitView.as_view()),
    path("transaction/debit/list/", FilterRawDebitTransactions.as_view()),
    # -----------------Raw Transfer------------------------ #
    path("transaction/transfer/", TransferRawStockView.as_view()),
    path("transaction/transfer/list/", FilterRawTransferTransactions.as_view()),
    # -----------------Raw------------------------
    path("lot-numbers/list/", ListLotNumberAndIdView.as_view()),
    # -----------------Formula--------------------- #
    path("formula/list/", ListFormula.as_view()),
    path("formula/create/", CreateFormula.as_view()),
    # -----------------Raw Product--------------------- #
    path("product/list/", ListRawProducts.as_view()),
    path("product/create/", CreateRawProduct.as_view()),
    # -----------------Raw Stock--------------------- #
    path("stock/all/", ViewAllStock.as_view()),
]
