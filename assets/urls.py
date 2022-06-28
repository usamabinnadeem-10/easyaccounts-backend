from django.urls import path

from .views import CreateAsset, DeleteAsset, EditAsset, ListAsset

urlpatterns = [
    path("create/", CreateAsset.as_view()),
    path("list/", ListAsset.as_view()),
    path("edit/<uuid:pk>/", EditAsset.as_view()),
    path("delete/<uuid:pk>/", DeleteAsset.as_view()),
]
