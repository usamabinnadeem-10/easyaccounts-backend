from django.urls import path

from .views import AddImageView, CreatePaymentView, DeletePictureView, ListPaymentView

urlpatterns = [
    path("create/", CreatePaymentView.as_view()),
    path("list/", ListPaymentView.as_view()),
    path("image/create/", AddImageView.as_view()),
    path("image/delete/<uuid:pk>/", DeletePictureView.as_view()),
]
