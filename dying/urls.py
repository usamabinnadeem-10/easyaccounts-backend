from django.urls import path

from .views import CreateDyingUnit, ListDyingUnit

urlpatterns = [
    # -----------------Dying Unit--------------------- #
    path("dying-unit/list/", ListDyingUnit.as_view()),
    path("dying-unit/create/", CreateDyingUnit.as_view()),
]
