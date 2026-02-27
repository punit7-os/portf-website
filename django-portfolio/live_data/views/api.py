from django.http import JsonResponse
from django.shortcuts import render
from live_data.services.weather_service import WeatherService
from live_data.services.crypto_service import CryptoService
from live_data.services.stock_service import StockService


def weather_api(request):
    data = WeatherService.get_current_weather()

    if request.headers.get("HX-Request"):
        return render(request, "live_data/partials/weather.html", data)

    return JsonResponse(data)


def crypto_api(request):
    data = CryptoService.get_prices()

    if request.headers.get("HX-Request"):
        return render(
            request,
            "live_data/partials/crypto.html",
            {"crypto": data}
        )

    return JsonResponse(data)


def stock_api(request):
    data = StockService.get_prices()

    if request.headers.get("HX-Request"):
        return render(
            request,
            "live_data/partials/stocks.html",
            {"stocks": data}
        )

    return JsonResponse(data)
