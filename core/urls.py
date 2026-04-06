from django.urls import path
from .views import DashboardView, ScadenzaListView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("scadenze/", ScadenzaListView.as_view(), name="scadenza_list"),
]