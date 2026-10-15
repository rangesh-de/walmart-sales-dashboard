"""
Prepare Walmart's weekly sales data (Kaggle: Walmart Recruiting - Store Sales Forecasting)
for a Tableau sales performance dashboard.

Steps:
  1. Validate the three files (columns, unique keys, Friday week dates).
  2. Merge sales with store type/size and weekly features (holidays, markdowns, economy).
  3. Build two dashboard tables: store-week and department-week.
  4. Compute the headline numbers: KPIs, holiday lift, the real peak week each year,
     and how much markdowns and the economy actually move sales.

Usage:
    python scripts/prepare_data.py              # expects data/train.csv, data/features.csv, data/stores.csv
    python scripts/prepare_data.py path/to/dir
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dashboard" / "data"

REQUIRED = {
    "train.csv": {"Store", "Dept", "Date", "Weekly_Sales", "IsHoliday"},
    "features.csv": {"Store", "Date", "Temperature", "Fuel_Price", "MarkDown1", "MarkDown2", "MarkDown3",
                     "MarkDown4", "MarkDown5", "CPI", "Unemployment", "IsHoliday"},
    "stores.csv": {"Store", "Type", "Size"},
}

# Holiday weeks as defined by the dataset (week-ending Fridays)
HOLIDAYS = {
    "2010-02-12": "Super Bowl", "2011-02-11": "Super Bowl", "2012-02-10": "Super Bowl",
    "2010-09-10": "Labor Day", "2011-09-09": "Labor Day", "2012-09-07": "Labor Day",
    "2010-11-26": "Thanksgiving", "2011-11-25": "Thanksgiving", "2012-11-23": "Thanksgiving",
    "2010-12-31": "Christmas", "2011-12-30": "Christmas", "2012-12-28": "Christmas",
}
MARKDOWNS = ["MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]


def load(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames = {}
    for name, cols in REQUIRED.items():
        path = data_dir / name
        if not path.exists():
            sys.exit(f"Missing {path}. Download the Kaggle files first (see data/README.md).")
        df = pd.read_csv(path)
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"{name} is missing columns: {sorted(missing)}")
        frames[name.removesuffix(".csv")] = df
    return frames


def validate(train: pd.DataFrame, features: pd.DataFrame, stores: pd.DataFrame) -> dict:
    checks = {}
    if train.duplicated(["Store", "Dept", "Date"]).any():
        raise ValueError("train.csv has duplicate Store-Dept-Date rows")
    if features.duplicated(["Store", "Date"]).any():
        raise ValueError("features.csv has duplicate Store-Date rows")
    if stores["Store"].duplicated().any():
        raise ValueError("stores.csv has duplicate stores")
    dates = pd.to_datetime(train["Date"])
    if (dates.dt.dayofweek != 4).any():
        raise ValueError("Expected every Date to be a Friday (week-ending date)")
    unknown = set(train["Store"]) - set(stores["Store"])
    if unknown:
        raise ValueError(f"Sales for stores not in stores.csv: {sorted(unknown)}")
    checks["negative_sales_rows"] = int((train["Weekly_Sales"] < 0).sum())     # returns exceeding sales
    checks["weeks"] = int(dates.nunique())
    return checks


def build(frames: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    train, features, stores = frames["train"].copy(), frames["features"].copy(), frames["stores"].copy()
    for df in (train, features):
        df["Date"] = pd.to_datetime(df["Date"])
    type_names = {"A": "A (large)", "B": "B (medium)", "C": "C (small)"}
    stores["StoreType"] = stores["Type"].map(type_names).fillna(stores["Type"])

    # Department-week table (the most detailed level)
    dept = train.merge(stores[["Store", "StoreType", "Size"]], on="Store", how="left")
    dept = dept.rename(columns={"Weekly_Sales": "WeeklySales"})
    dept["IsReturnWeek"] = dept["WeeklySales"] < 0

    # Store-week table: departments summed, then joined to the weekly features
    store_week = (train.groupby(["Store", "Date"], as_index=False)
                  .agg(WeeklySales=("Weekly_Sales", "sum"), Departments=("Dept", "nunique")))
    feats = features.drop(columns=["IsHoliday"])
    feats["MarkdownTotal"] = feats[MARKDOWNS].fillna(0).clip(lower=0).sum(axis=1)
    feats["MarkdownDataAvailable"] = feats[MARKDOWNS].notna().any(axis=1)
    store_week = (store_week
                  .merge(feats[["Store", "Date", "Temperature", "Fuel_Price", "CPI", "Unemployment",
                                "MarkdownTotal", "MarkdownDataAvailable"]], on=["Store", "Date"], how="left")
                  .merge(stores[["Store", "StoreType", "Size"]], on="Store", how="left"))

    for df in (store_week, dept):
        df["Holiday"] = df["Date"].dt.strftime("%Y-%m-%d").map(HOLIDAYS).fillna("None")
        df["IsHolidayWeek"] = df["Holiday"] != "None"
        df["Year"] = df["Date"].dt.year
        df["WeekOfYear"] = df["Date"].dt.isocalendar().week.astype(int)

    store_week["SalesPerSqFt"] = store_week["WeeklySales"] / store_week["Size"]
    store_week["TemperatureC"] = ((store_week["Temperature"] - 32) * 5 / 9).round(1)
    return store_week, dept


def headline_numbers(store_week: pd.DataFrame) -> dict:
    sw = store_week
    weekly_total = sw.groupby("Date")["WeeklySales"].sum()
    k = {
        "stores": int(sw["Store"].nunique()),
        "weeks": int(sw["Date"].nunique()),
        "first_week": str(sw["Date"].min().date()),
        "last_week": str(sw["Date"].max().date()),
        "total_sales": round(float(sw["WeeklySales"].sum()), 0),
        "avg_weekly_sales_all_stores": round(float(weekly_total.mean()), 0),
        "avg_weekly_sales_per_store": round(float(sw["WeeklySales"].mean()), 0),
    }

    # Like-for-like year over year: only the weeks of the year present in every year
    weeks_by_year = sw.groupby("Year")["WeekOfYear"].apply(set)
    common = set.intersection(*weeks_by_year) if len(weeks_by_year) else set()
    lfl = sw[sw["WeekOfYear"].isin(common)].groupby("Year")["WeeklySales"].sum()
    for year, value in lfl.items():
        k[f"sales_{year}_common_weeks"] = round(float(value), 0)
    k["common_weeks_used"] = f"week {min(common)}-{max(common)}" if common else "none"

    # Holiday lift: chain-wide sales in each holiday week vs the average non-holiday week that year
    chain = sw.groupby(["Date", "Year", "Holiday"], as_index=False)["WeeklySales"].sum()
    normal = chain[chain["Holiday"] == "None"].groupby("Year")["WeeklySales"].mean()
    hol = chain[chain["Holiday"] != "None"].copy()
    hol["lift_pct"] = 100 * (hol["WeeklySales"] / hol["Year"].map(normal) - 1)
    for name, g in hol.groupby("Holiday"):
        k[f"holiday_lift_pct_{name.lower().replace(' ', '_')}"] = round(float(g["lift_pct"].mean()), 1)

    # The real peak week of each year (vs the dataset's "Christmas" flag)
    # Only years whose data includes December; otherwise the "peak" is just the best week available
    full_years = chain.loc[chain["Date"].dt.month == 12, "Year"].unique()
    chain_full = chain[chain["Year"].isin(full_years)]
    peaks = chain_full.loc[chain_full.groupby("Year")["WeeklySales"].idxmax(), ["Year", "Date", "Holiday"]]
    for _, r in peaks.iterrows():
        k[f"peak_week_{r['Year']}"] = f"{r['Date'].date()} (flagged holiday: {r['Holiday']})"

    # Store type: does size explain the gap?
    by_type = sw.groupby("StoreType").agg(avg_weekly=("WeeklySales", "mean"), per_sqft=("SalesPerSqFt", "mean"))
    for t, r in by_type.iterrows():
        k[f"avg_weekly_sales_type_{t[0]}"] = round(float(r["avg_weekly"]), 0)
        k[f"sales_per_sqft_type_{t[0]}"] = round(float(r["per_sqft"]), 2)

    # Do markdowns and the economy move sales? Correlation with each store's own deviation from
    # its average week, so big stores don't dominate.
    sw = sw.copy()
    sw["SalesVsStoreAvg"] = sw["WeeklySales"] / sw.groupby("Store")["WeeklySales"].transform("mean") - 1
    for col in ["MarkdownTotal", "Fuel_Price", "CPI", "Unemployment", "TemperatureC"]:
        subset = sw[sw["MarkdownDataAvailable"]] if col == "MarkdownTotal" else sw
        k[f"corr_sales_vs_{col.lower()}"] = round(float(subset["SalesVsStoreAvg"].corr(subset[col])), 3)
    return k


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data"
    frames = load(data_dir)
    checks = validate(frames["train"], frames["features"], frames["stores"])
    store_week, dept = build(frames)
    k = headline_numbers(store_week)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    store_week.to_csv(OUT_DIR / "store_weekly.csv", index=False)
    dept.to_csv(OUT_DIR / "dept_weekly.csv", index=False)

    lines = ["# Headline numbers\n",
             "Use these to check the Tableau dashboard (all filters cleared) and to write the README findings.\n",
             f"- Data checks: {checks['weeks']} weeks, {checks['negative_sales_rows']:,} department-weeks "
             "with negative sales (returns), kept as-is\n"]
    lines += [f"- **{key}**: {value:,}" if isinstance(value, (int, float)) else f"- **{key}**: {value}"
              for key, value in k.items()]
    (ROOT / "dashboard" / "kpi_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"store_weekly.csv  {len(store_week):,} rows")
    print(f"dept_weekly.csv   {len(dept):,} rows\n")
    for key, value in k.items():
        print(f"  {key:<34} {value:,}" if isinstance(value, (int, float)) else f"  {key:<34} {value}")


if __name__ == "__main__":
    main()
