from django.urls import path

from .views import (
    AddImageView,
    CreatePaymentView,
    DeletePaymentView,
    DeletePictureView,
    ListPaymentView,
    UpdatePaymentView,
)

urlpatterns = [
    path("create/", CreatePaymentView.as_view()),
    path("edit/<uuid:pk>/", UpdatePaymentView.as_view()),
    path("delete/<uuid:pk>/", DeletePaymentView.as_view()),
    path("list/", ListPaymentView.as_view()),
    # -----------------IMAGE---------------------- #
    path("image/create/", AddImageView.as_view()),
    path("image/delete/<uuid:pk>/", DeletePictureView.as_view()),
]
