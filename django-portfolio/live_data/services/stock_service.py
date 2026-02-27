from django.core.cache import cache
from datetime import datetime, time
import pytz
import requests


class StockService:

    CACHE_KEY = "live_yahoo_stock_data"
    CACHE_TIMEOUT = 60

    INDIAN_STOCKS = {
        "TCS.NS": "TCS",
        "INFY.NS": "Infosys",
        "RELIANCE.NS": "Reliance"
    }

    US_STOCKS = {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "TSLA": "Tesla"
    }

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    @staticmethod
    def is_nse_open():
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist).time()
        return time(9, 15) <= now <= time(15, 30)

    @staticmethod
    def is_us_open():
        est = pytz.timezone("US/Eastern")
        now = datetime.now(est).time()
        return time(9, 30) <= now <= time(16, 0)

    @staticmethod
    def fetch_stock(symbol, market_open):

        interval = "1m" if market_open else "1d"
        range_value = "1d" if market_open else "5d"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

        params = {
            "interval": interval,
            "range": range_value
        }

        response = requests.get(
            url,
            params=params,
            headers=StockService.HEADERS,
            timeout=5
        )

        if response.status_code != 200:
            return None

        data = response.json()

        result = data.get("chart", {}).get("result")
        if not result:
            return None

        result = result[0]
        meta = result.get("meta", {})
        indicators = result.get("indicators", {}).get("quote", [{}])[0]

        closes = [c for c in indicators.get("close", []) if c is not None]

        if not closes:
            return None

        current_price = closes[-1]
        previous_close = meta.get("previousClose", current_price)

        change_percent = ((current_price - previous_close) / previous_close) * 100

        return {
            "price": round(current_price, 2),
            "change": round(change_percent, 2),
            "high": round(meta.get("regularMarketDayHigh", current_price), 2),
            "low": round(meta.get("regularMarketDayLow", current_price), 2),
            "volume": int(meta.get("regularMarketVolume", 0)),
            "sparkline": closes[-15:]  # lightweight history
        }

    @staticmethod
    def get_prices():

        cached = cache.get(StockService.CACHE_KEY)
        if cached:
            return cached

        try:
            nse_open = StockService.is_nse_open()
            us_open = StockService.is_us_open()

            indian_results = []
            us_results = []

            for symbol, name in StockService.INDIAN_STOCKS.items():
                data = StockService.fetch_stock(symbol, nse_open)
                if data:
                    data["market"] = "India"
                    data["delayed"] = not nse_open
                    indian_results.append((name, data))

            for symbol, name in StockService.US_STOCKS.items():
                data = StockService.fetch_stock(symbol, us_open)
                if data:
                    data["market"] = "US"
                    data["delayed"] = not us_open
                    us_results.append((name, data))

            # Alternate India → US
            results = {}
            max_len = max(len(indian_results), len(us_results))

            for i in range(max_len):
                if i < len(indian_results):
                    name, data = indian_results[i]
                    results[name] = data
                if i < len(us_results):
                    name, data = us_results[i]
                    results[name] = data

            cache.set(StockService.CACHE_KEY, results, StockService.CACHE_TIMEOUT)

            return results

        except Exception:
            return {
                "error": "Unable to fetch Yahoo Finance data at the moment."
            }
