import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================================
# FILE PATHS
# =========================================

COMMODITY_PATH = os.path.join(
    BASE_DIR,
    "Major Commodities",
    "commodities_dataset.csv"
)

SUPPLY_PATH = os.path.join(
    BASE_DIR,
    "Global Supply Chain Disruption and Resiliance",
    "global_supply_chain_disruption_v1.csv"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "final_trade_dataset.csv"
)

# =========================================
# LOAD DATA
# =========================================

print("Loading Commodities Dataset...")
commodities = pd.read_csv(COMMODITY_PATH)

print("Loading Supply Chain Dataset...")
supply = pd.read_csv(SUPPLY_PATH)

# =========================================
# CLEAN & SELECT COLUMNS
# =========================================

print("Cleaning Commodities Data...")

commodities = commodities[
    ["Date", "Crude_Oil_Brent_('Close', 'BZ=F')"]
].copy()

commodities.rename(columns={
    "Crude_Oil_Brent_('Close', 'BZ=F')": "Brent_Oil_Price"
}, inplace=True)

commodities["Date"] = pd.to_datetime(commodities["Date"])

# Drop rows where oil price is missing
commodities = commodities.dropna(subset=["Brent_Oil_Price"])


print("Cleaning Supply Chain Data...")

supply = supply[
    [
        "Order_Date",
        "Delay_Days",
        "Geopolitical_Risk_Index",
        "Shipping_Cost_USD",
        "Transportation_Mode",
        "Route_Type"
    ]
].copy()

supply.rename(columns={
    "Order_Date": "Date",
    "Shipping_Cost_USD": "Shipping_Cost",
    "Route_Type": "Trade_Route",
    "Transportation_Mode": "Shipping_Mode"
}, inplace=True)

supply["Date"] = pd.to_datetime(supply["Date"])

# =========================================
# MERGE DATASETS
# =========================================

print("Merging Datasets...")

merged = pd.merge(
    supply,
    commodities,
    on="Date",
    how="inner"
)

# =========================================
# OPTIMIZE MEMORY (AWS SAFE)
# =========================================

print("Optimizing Memory...")

merged["Shipping_Cost"] = merged["Shipping_Cost"].astype("float32")
merged["Brent_Oil_Price"] = merged["Brent_Oil_Price"].astype("float32")
merged["Geopolitical_Risk_Index"] = merged["Geopolitical_Risk_Index"].astype("float32")
merged["Delay_Days"] = merged["Delay_Days"].astype("int16")

merged["Trade_Route"] = merged["Trade_Route"].astype("category")
merged["Shipping_Mode"] = merged["Shipping_Mode"].astype("category")

# =========================================
# SAVE FINAL FILE
# =========================================

merged.to_csv(OUTPUT_PATH, index=False)

print("===================================")
print("ETL Completed Successfully ✅")
print("Final file saved to:")
print(OUTPUT_PATH)
print("Total Rows:", len(merged))
print("===================================")