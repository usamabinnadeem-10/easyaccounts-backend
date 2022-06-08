from django.urls import path

from .views import CreatePaymentView, DeletePictureView, ListPaymentView

urlpatterns = [
    path("create/", CreatePaymentView.as_view()),
    path("list/", ListPaymentView.as_view()),
    path("delete/<uuid:pk>/", DeletePictureView.as_view()),
]
