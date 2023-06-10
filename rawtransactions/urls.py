from django.urls import path

from .views import (
    CreateFormula,
    CreateRawProduct,
    CreateRawTransaction,
    EditUpdateDeleteRawDebitTransactionView,
    EditUpdateDeleteRawTransactionView,
    EditUpdateDeleteRawTransferTransactionView,
    FilterRawDebitTransactions,
    FilterRawTransactions,
    FilterRawTransferTransactions,
    ListFormula,
    ListLotNumberAndIdView,
    ListRawProducts,
    RawDebitView,
    RawTransactionLotDetail,
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
    path(
        "transaction/debit/<uuid:pk>/", EditUpdateDeleteRawDebitTransactionView.as_view()
    ),
    # -----------------Raw Transfer------------------------ #
    path("transaction/transfer/", TransferRawStockView.as_view()),
    path("transaction/transfer/list/", FilterRawTransferTransactions.as_view()),
    path(
        "transaction/transfer/<uuid:pk>/",
        EditUpdateDeleteRawTransferTransactionView.as_view(),
    ),
    # -----------------Lot number and lot stock------------------------
    path("lot-numbers/list/", ListLotNumberAndIdView.as_view()),
    path("lot/detail/<uuid:pk>/", RawTransactionLotDetail.as_view()),
    # -----------------Formula--------------------- #
    path("formula/list/", ListFormula.as_view()),
    path("formula/create/", CreateFormula.as_view()),
    # -----------------Raw Product--------------------- #
    path("product/list/", ListRawProducts.as_view()),
    path("product/create/", CreateRawProduct.as_view()),
    # -----------------Raw Stock--------------------- #
    path("stock/all/", ViewAllStock.as_view()),
]
