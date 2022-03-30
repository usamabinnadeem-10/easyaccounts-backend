from django.urls import path

from .views import CreateDyingUnit, IssueForDyingView, ListDyingUnit, ListIssuedLotsView

urlpatterns = [
    # -----------------Dying Unit--------------------- #
    path("dying-unit/list/", ListDyingUnit.as_view()),
    path("dying-unit/create/", CreateDyingUnit.as_view()),
    # -----------------Dying Issue--------------------- #
    path("issued-lots/list/", ListIssuedLotsView.as_view()),
    path("issue/create/", IssueForDyingView.as_view()),
]
