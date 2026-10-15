import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from prepare_data import build, headline_numbers, validate  # noqa: E402

DATES = pd.date_range("2010-11-05", "2011-01-07", freq="W-FRI").strftime("%Y-%m-%d")


def frames():
    stores = pd.DataFrame({"Store": [1, 2], "Type": ["A", "C"], "Size": [200_000, 50_000]})
    train = []
    for store, base in [(1, 1000.0), (2, 250.0)]:
        for d in DATES:
            mult = 2.0 if d == "2010-12-24" else 1.5 if d == "2010-11-26" else 1.0
            for dept in (1, 2):
                train.append((store, dept, d, base * mult, d in ("2010-11-26", "2010-12-31")))
    train = pd.DataFrame(train, columns=["Store", "Dept", "Date", "Weekly_Sales", "IsHoliday"])
    train.loc[0, "Weekly_Sales"] = -50.0                                   # a return-heavy week
    feats = []
    for store in (1, 2):
        for d in DATES:
            md = [100.0, np.nan, 50.0, np.nan, -10.0] if d >= "2010-12-01" else [np.nan] * 5
            feats.append((store, d, 50.0, 3.0, *md, 210.0, 8.0, False))
    features = pd.DataFrame(feats, columns=["Store", "Date", "Temperature", "Fuel_Price", "MarkDown1", "MarkDown2",
                                            "MarkDown3", "MarkDown4", "MarkDown5", "CPI", "Unemployment", "IsHoliday"])
    return {"train": train, "features": features, "stores": stores}


def test_validate_counts_returns_and_weeks():
    f = frames()
    checks = validate(f["train"], f["features"], f["stores"])
    assert checks == {"negative_sales_rows": 1, "weeks": len(DATES)}


def test_validate_rejects_duplicates_and_non_fridays():
    f = frames()
    with pytest.raises(ValueError, match="duplicate"):
        validate(pd.concat([f["train"], f["train"].head(1)]), f["features"], f["stores"])
    bad = f["train"].copy()
    bad.loc[0, "Date"] = "2010-11-06"                                      # a Saturday
    with pytest.raises(ValueError, match="Friday"):
        validate(bad, f["features"], f["stores"])


def test_build_store_week_sums_departments_and_joins():
    store_week, dept = build(frames())
    assert len(store_week) == 2 * len(DATES) and len(dept) == 2 * 2 * len(DATES)
    row = store_week[(store_week["Store"] == 2) & (store_week["Date"] == "2010-12-24")].iloc[0]
    assert row["WeeklySales"] == 1000.0                                    # 2 depts x 250 x 2.0
    assert row["StoreType"] == "C (small)"
    assert row["SalesPerSqFt"] == pytest.approx(1000 / 50_000)


def test_markdowns_missing_treated_as_zero_and_negatives_clipped():
    store_week, _ = build(frames())
    dec = store_week[store_week["Date"] == "2010-12-10"].iloc[0]
    nov = store_week[store_week["Date"] == "2010-11-12"].iloc[0]
    assert dec["MarkdownTotal"] == 150.0 and bool(dec["MarkdownDataAvailable"]) is True
    assert nov["MarkdownTotal"] == 0.0 and bool(nov["MarkdownDataAvailable"]) is False


def test_holiday_names_and_peak_week_vs_christmas_flag():
    store_week, _ = build(frames())
    assert set(store_week.loc[store_week["IsHolidayWeek"], "Holiday"]) == {"Thanksgiving", "Christmas"}
    k = headline_numbers(store_week)
    assert k["peak_week_2010"] == "2010-12-24 (flagged holiday: None)"     # real peak is not the flagged week
    assert k["holiday_lift_pct_thanksgiving"] > 0
    assert k["holiday_lift_pct_christmas"] < 1                             # flagged week is ordinary


def test_like_for_like_uses_only_shared_weeks():
    store_week, _ = build(frames())
    k = headline_numbers(store_week)
    # 2010 has weeks 44-52, 2011 has week 1 only: no week of the year appears in both
    assert k["common_weeks_used"] == "none"
