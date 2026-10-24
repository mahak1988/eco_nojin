from pathlib import Path

import numpy as np
import pandas as pd

cimmyt_path = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
df = pd.read_excel(cimmyt_path, sheet_name="Sheet1")

# Records per district per season
print("=== Records per district per season ===")
pivot = df.groupby(["District", "Year"]).size().unstack(fill_value=0)
print(pivot)

# Unique coords per district
print("\n=== Unique lat/lon per district ===")
for district in sorted(df["District"].unique()):
    sub = df[df["District"] == district]
    unique_coords = sub.groupby(["Latitude", "Longitude"]).ngroups
    print(f"  {district}: {len(sub)} records, {unique_coords} unique coords, seasons: {sorted(sub['Year'].unique())}")

# Coordinate precision
print("\n=== Coordinate precision ===")
print(f"Latitude decimals: {df['Latitude'].apply(lambda x: len(str(x).split('.')[1]) if '.' in str(x) else 0).describe()}")
print(f"Longitude decimals: {df['Longitude'].apply(lambda x: len(str(x).split('.')[1]) if '.' in str(x) else 0).describe()}")

# Sowing/Harvest date ranges per season
print("\n=== Sowing/Harvest dates per season ===")
for season in sorted(df["Year"].unique()):
    sub = df[df["Year"] == season]
    sowing = pd.to_datetime(sub["SowingDate"])
    harvest = pd.to_datetime(sub["HarvestDate"])
    print(f"  {season}: sowing {sowing.min().date()} to {sowing.max().date()}, harvest {harvest.min().date()} to {harvest.max().date()}, n={len(sub)}")

# Check for yield outliers
print("\n=== Yield outlier analysis ===")
print("Yield percentiles:")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"  {p}th: {np.percentile(df['GrainYield'], p):.3f}")
print(f"\nYields > 6.5 t/ha: {(df['GrainYield'] > 6.5).sum()}")
print(f"Yields > 7.0 t/ha: {(df['GrainYield'] > 7.0).sum()}")
print(f"Yields < 2.0 t/ha: {(df['GrainYield'] < 2.0).sum()}")

# Check missing weather columns
print("\n=== Missing weather values ===")
for col in ["Prcp_Monsoon", "Jan_Srad", "Feb_Srad", "Nov_Tmax", "Dec_Tmax", "Mar_Tmax", "Apr_Tmax"]:
    missing = df[col].isna().sum()
    print(f"  {col}: {missing} missing ({100*missing/len(df):.1f}%)")

# Sowing/Harvest date validity
sowing = pd.to_datetime(df["SowingDate"])
harvest = pd.to_datetime(df["HarvestDate"])
print(f"\nSowing before harvest: {(harvest >= sowing).all()}")
print(f"Season length stats: {(harvest - sowing).dt.days.describe()}")
