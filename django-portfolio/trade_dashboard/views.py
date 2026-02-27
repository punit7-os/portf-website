import os
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

# =========================================
# Memory-Optimized Data Loader (EC2 Safe)
# =========================================

CSV_PATH = os.path.join(
    settings.BASE_DIR,
    "trade_dashboard",
    "data",
    "final_trade_dataset.csv"
)

_cached_df = None


def load_dataframe():
    global _cached_df

    if _cached_df is None:
        _cached_df = pd.read_csv(
            CSV_PATH,
            usecols=[
                "Date",
                "Trade_Route",
                "Shipping_Mode",
                "Shipping_Cost",
                "Delay_Days",
                "Geopolitical_Risk_Index",
                "Brent_Oil_Price",
            ],
            dtype={
                "Trade_Route": "category",
                "Shipping_Mode": "category",
                "Shipping_Cost": "float32",
                "Delay_Days": "int16",
                "Geopolitical_Risk_Index": "float32",
                "Brent_Oil_Price": "float32",
            },
            parse_dates=["Date"],
        )

    return _cached_df


# =========================================
# Dashboard View
# =========================================

def dashboard(request):
    return render(request, "trade_dashboard/dashboard.html")

# =========================================
# HTMX Shipment Table (Filtered)
# =========================================

def shipment_table(request):
    df = load_dataframe()

    route = request.GET.get("route")
    mode = request.GET.get("mode")
    sort_by = request.GET.get("sort", "Date")
    order = request.GET.get("order", "desc")

    if route:
        df = df[df["Trade_Route"] == route]

    if mode:
        df = df[df["Shipping_Mode"] == mode]

    # Valid sortable columns
    valid_columns = {
        "Date": "Date",
        "Cost": "Shipping_Cost",
        "Delay": "Delay_Days",
        "Risk": "Geopolitical_Risk_Index"
    }

    if sort_by in valid_columns:
        column = valid_columns[sort_by]
        ascending = True if order == "asc" else False
        df = df.sort_values(column, ascending=ascending)
    else:
        df = df.sort_values("Date", ascending=False)

    df = df.head(50)

    rows = df.to_dict("records")

    return render(
        request,
        "trade_dashboard/partials/shipment_table.html",
        {
            "rows": rows,
            "current_sort": sort_by,
            "current_order": order
        }
    )

def dashboard_data(request):
    df = load_dataframe()
   
    route = request.GET.get("route")
    mode = request.GET.get("mode")

    if route:
        df = df[df["Trade_Route"] == route]

    if mode:
        df = df[df["Shipping_Mode"] == mode]

    # ===== Avg Delay =====
    avg_delay = round(df["Delay_Days"].mean(), 2)

    # ===== Trend Calculation (Delay) =====
    trend_percent = 0
    trend_direction = "flat"
    trend_color = "text-slate-400"

    if len(df) > 1:
        sorted_df = df.sort_values("Date")
        grouped_delay = sorted_df.groupby("Date")["Delay_Days"].mean().reset_index()

        if len(grouped_delay) >= 2:
            latest = grouped_delay.iloc[-1]["Delay_Days"]
            previous = grouped_delay.iloc[-2]["Delay_Days"]

            if previous != 0:
                trend_percent = round(((latest - previous) / previous) * 100, 2)

                if trend_percent > 0:
                    trend_direction = "up"
                    trend_color = "text-red-400"
                elif trend_percent < 0:
                    trend_direction = "down"
                    trend_color = "text-green-400"

    # ===== Other Metrics =====
    total_volume = len(df)
    avg_risk = round(df["Geopolitical_Risk_Index"].mean(), 2)
    snapshot_size = len(df)

    if len(df) > 1:
        corr_value = df["Shipping_Cost"].corr(df["Geopolitical_Risk_Index"])

        # ===== Oil vs Shipping Correlation =====

        if pd.isna(corr_value):
            correlation = 0
        else:
            correlation = round(float(corr_value), 4)

        if len(df) > 1:
            oil_corr_value = df["Shipping_Cost"].corr(df["Brent_Oil_Price"])
            if pd.isna(oil_corr_value):
                oil_correlation = 0
            else:
                oil_correlation = round(float(oil_corr_value), 4)
        else:
            oil_correlation = 0
    else:
        correlation = 0

    # ===== Line Chart =====
    # ===== Line Chart (Including Oil) =====
    # ===== Line Chart (Monthly Aggregation for clarity) =====
    # ===== Line Chart (Monthly Aggregation for clarity) =====
    df["Month"] = df["Date"].dt.to_period("M")

    time_group = df.groupby("Month").agg({
        "Shipping_Cost": "mean",
        "Delay_Days": "mean",
        "Brent_Oil_Price": "mean"
    }).reset_index()

    line_chart_data = {
        "labels": time_group["Month"].astype(str).tolist(),
        "costs": time_group["Shipping_Cost"].round(2).tolist(),
        "delays": time_group["Delay_Days"].round(2).tolist(),
        "oil": time_group["Brent_Oil_Price"].round(2).tolist(),
    }

    # ===== Bar Chart =====
    route_group = df.groupby("Trade_Route")[
        "Geopolitical_Risk_Index"
    ].mean().reset_index()

    bar_chart_data = {
        "routes": route_group["Trade_Route"].tolist(),
        "risks": route_group["Geopolitical_Risk_Index"].round(2).tolist(),
    }

    return render(
        request,
        "trade_dashboard/partials/dashboard_data.html",
        {
            "avg_delay": avg_delay,
            "total_volume": total_volume,
            "avg_risk": avg_risk,
            "correlation": correlation,
            "line_chart_data": line_chart_data,
            "bar_chart_data": bar_chart_data,
            "trend_percent": trend_percent,
            "trend_direction": trend_direction,
            "trend_color": trend_color,
            "oil_correlation": oil_correlation,
            "snapshot_size": snapshot_size,
        }
    )