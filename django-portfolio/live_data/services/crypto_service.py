from django.core.cache import cache
from .base import safe_get, APIServiceError


class CryptoService:

    CACHE_KEY = "live_binance_crypto"

    # Keep cache safely beyond minute boundary
    CACHE_TIMEOUT = 60  # seconds

    SYMBOLS = {
        "BTCUSDT": "Bitcoin",
        "ETHUSDT": "Ethereum",
        "BNBUSDT": "BNB",
        "SOLUSDT": "Solana",
        "XRPUSDT": "XRP"
    }

    @staticmethod
    def get_prices():

        # 🔹 Return cached data instantly if available
        cached_data = cache.get(CryptoService.CACHE_KEY)
        if cached_data:
            return cached_data

        results = {}

        try:
            # 🔹 SINGLE REQUEST FOR ALL 24h TICKERS (faster)
            ticker_url = "https://api.binance.com/api/v3/ticker/24hr"
            all_tickers = safe_get(ticker_url)

            # Convert to dictionary for fast lookup
            ticker_map = {item["symbol"]: item for item in all_tickers}

            for symbol, name in CryptoService.SYMBOLS.items():

                ticker_data = ticker_map.get(symbol)
                if not ticker_data:
                    continue

                # 🔹 Kline request (15 candles only)
                kline_url = "https://api.binance.com/api/v3/klines"
                kline_data = safe_get(
                    kline_url,
                    params={
                        "symbol": symbol,
                        "interval": "1m",
                        "limit": 15
                    }
                )

                closes = [float(candle[4]) for candle in kline_data]

                results[name] = {
                    "price": float(ticker_data.get("lastPrice", 0)),
                    "change_24h": float(ticker_data.get("priceChangePercent", 0)),
                    "volume": float(ticker_data.get("volume", 0)),
                    "high_24h": float(ticker_data.get("highPrice", 0)),
                    "low_24h": float(ticker_data.get("lowPrice", 0)),
                    "sparkline": closes
                }

            # 🔹 Cache for fixed 70 seconds
            cache.set(
                CryptoService.CACHE_KEY,
                results,
                CryptoService.CACHE_TIMEOUT
            )

            return results

        except APIServiceError:
            return {
                "error": "Unable to fetch Binance data at the moment."
            }
