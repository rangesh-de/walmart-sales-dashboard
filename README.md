# Walmart Store Sales Performance Dashboard

A Tableau dashboard on Walmart's public weekly sales for **45 stores and about 80 departments (Feb 2010 – Oct 2012)**, built to answer what a regional sales director asks: how are we trending, which stores and departments carry the business, and do holidays and markdowns actually pay off?

**Skills shown:** data validation and merging in pandas, like-for-like time comparisons, Tableau LOD expressions, drill-down hierarchies, filter actions, annotated storytelling, and checking a dataset's own labels against the data.

## Dashboard

> Add after publishing: **[View on Tableau Public](LINK)**
>
> ![Dashboard](dashboard/screenshot.png)

- KPI tiles: total sales, average week, like-for-like year-over-year growth, sales per square foot
- Weekly trend with holiday weeks highlighted and the true peak week annotated
- Holiday lift: how much each holiday week beats a normal week
- Store type: is the gap between large and small stores about size or efficiency?
- Top stores with a store type → store drill-down
- Markdown spend vs sales, and department seasonality (second page)

## Key findings

> Fill in from `dashboard/kpi_check.md` after running the prep script on the real files. Each finding = a number + what a manager should do. Example format:
> - **The dataset's "Christmas" week is not the peak.** Sales peak the week before; the flagged week is the post-holiday lull. Forecasts built on the flag would staff and stock the wrong week.
> - **Thanksgiving week runs X% above a normal week**, the biggest lift of any holiday.

- 
- 
- 

## How the data is prepared

`scripts/prepare_data.py`:

1. **Validates** the three Kaggle files: required columns, unique store-department-week keys, every date a Friday, every store known.
2. **Merges** weekly sales with store type and size, and with weekly features (temperature, fuel price, CPI, unemployment, markdowns).
3. **Builds two tables:** store-week (6,435 rows) for most charts and department-week (~420k rows) for department detail.
4. **Computes the headline numbers:** like-for-like growth, holiday lift, the real peak week of each year, sales per square foot by store type, and how strongly markdowns and the economy move sales.

Data decisions:
- **Markdowns** exist only from Nov 2011. Missing values mean "no data", not "no markdown", so markdown analysis is limited to that period.
- **Negative sales** (returns larger than sales in a department-week) are kept, so totals aren't overstated.
- **Holiday names** come from the dataset's documented holiday weeks, so charts show "Thanksgiving" rather than `True`.
- **Economic correlations** compare each store with its own average week, so large stores don't dominate the result.

## How to run it

```bash
pip install -r requirements.txt
# 1. Download train.csv, features.csv and stores.csv into data/ (see data/README.md)
python scripts/prepare_data.py
python -m pytest
# 2. Build the dashboard: docs/TABLEAU_DASHBOARD.md
```

## Project structure

```
├── dashboard/                   Prepared data + headline numbers (generated), screenshot
├── data/                        Raw Kaggle files (not committed)
├── docs/TABLEAU_DASHBOARD.md    Step-by-step build guide + interview talking points
├── scripts/prepare_data.py      Validate, merge, build tables, compute headline numbers
└── tests/test_prepare.py
```

## Limitations

- Stores are anonymized and the data ends in 2012, so this shows method and patterns, not current Walmart performance.
- Markdown types (MarkDown1–5) are not described by Walmart, so they're analyzed as a total.
- Correlation is not causation: markdowns cluster around holidays, so their effect can't be separated cleanly with this data.

## Data source

[Walmart Recruiting – Store Sales Forecasting](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting) on Kaggle (Walmart's recruiting competition data).
