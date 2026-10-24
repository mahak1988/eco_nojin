from pathlib import Path

import pandas as pd
import requests

# Test NASA POWER
print("=== Testing NASA POWER ===")
try:
    resp = requests.get(
        "https://power.larc.nasa.gov/api/temporal/daily/point",
        params={
            "parameters": "T2M_MIN,T2M_MAX,PRECTOTCORR,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_PAR_TOT",
            "community": "RE",
            "format": "JSON",
            "start": "20170115",
            "end": "20170120",
            "latitude": 26.6062,
            "longitude": 85.7098,
        },
        timeout=15,
    )
    print(f"NASA POWER Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        params = data.get("properties", {}).get("parameter", {})
        print(f"NASA POWER params: {list(params.keys())}")
        for key in list(params.keys())[:2]:
            vals = params[key]
            first_keys = list(vals.keys())[:3]
            print(f"  {key}: {first_keys}")
except Exception as e:
    print(f"NASA POWER Error: {type(e).__name__}: {e}")

# Read CIMMYT data
print("\n=== Reading CIMMYT Data ===")
cimmyt_path = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
df = pd.read_excel(cimmyt_path, sheet_name="Sheet1")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print("\nGrainYield stats:")
print(df["GrainYield"].describe())
print(f"\nGrainYield min: {df['GrainYield'].min()}, max: {df['GrainYield'].max()}")
print(f"\nZero yields: {(df['GrainYield'] == 0).sum()}")
print(f"Negative yields: {(df['GrainYield'] < 0).sum()}")
print(f"NaN yields: {df['GrainYield'].isna().sum()}")
print(f"\nDistricts: {sorted(df['District'].unique())}")
print(f"States: {sorted(df['State'].unique())}")
print(f"Seasons (Year): {sorted(df['Year'].unique())}")
print(f"\nUnique lat/lon pairs: {len(df.groupby(['Latitude', 'Longitude']).ngroups)}")
print(f"Max fields per lat/lon: {df.groupby(['Latitude', 'Longitude']).size().max()}")
print(f"Unique Field_IDs: {df['Field_ID'].nunique()}")
print(f"Total records: {len(df)}")

# Show a sample record
print("\n=== Sample Record ===")
sample = df.iloc[0]
print(sample[["Field_ID", "Year", "District", "State", "SowingDate", "HarvestDate", "GrainYield", "Latitude", "Longitude"]].to_dict())
print(f"\nSowingDate type: {type(sample['SowingDate'])}")
print(f"HarvestDate type: {type(sample['HarvestDate'])}")

# Check for extreme yields
print("\n=== Yield Distribution ===")
print(f"Bottom 5 yields: {sorted(df['GrainYield'])[:5]}")
print(f"Top 5 yields: {sorted(df['GrainYield'])[-5:]}")
print(f"Yield > 10 t/ha: {(df['GrainYield'] > 10).sum()}")
print(f"Yield > 15 t/ha: {(df['GrainYield'] > 15).sum()}")
