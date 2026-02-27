from django.urls import path
from live_data.views.api import weather_api, crypto_api, stock_api

app_name = "live_data_api"

urlpatterns = [
    path("weather/", weather_api, name="weather"),
    path("crypto/", crypto_api, name="crypto"),
    path("stocks/", stock_api, name="stocks"),
]
