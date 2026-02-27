from django.urls import path
from live_data.views.pages import dashboard

app_name = "live_data_pages"

urlpatterns = [
    path("", dashboard, name="dashboard"),
]
