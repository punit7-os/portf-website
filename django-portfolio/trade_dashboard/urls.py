from django.urls import path
from . import views

app_name = "trade_dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("shipments/", views.shipment_table, name="shipment_table"),
    path("dashboard-data/", views.dashboard_data, name="dashboard_data"),

]
