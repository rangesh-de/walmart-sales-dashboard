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

Walmart weekly sales for 45 stores, Feb 2010 – Oct 2012: $6.74B in total, about $47M a week across the chain.

- **The dataset's "Christmas" week is the wrong week.** Sales actually peaked the week ending Dec 24, 2010 and Dec 23, 2011, neither of which is flagged as a holiday. The flagged "Christmas" week (the one after Christmas) runs **8.1% below** a normal week. A forecast or staffing plan built on the flag would prepare for the lull, not the rush.
- **Thanksgiving is the only holiday that really moves sales.** Thanksgiving week runs **40.6% above** a normal week. The Super Bowl adds 3.7%, and Labor Day 0.2%, which is effectively nothing. Promotion and staffing budgets should be weighted heavily toward late November and the week before Christmas.
- **Small stores use their space best.** Type C stores sell **$11.66 per square foot** a week, **51% more** than large Type A stores ($7.74), even though their total sales are a third as big. Raw sales rankings make the big stores look best; per square foot tells a different story about where new space would pay off.
- **The economy barely moves weekly sales.** Correlations between each store's weekly sales and fuel price (−0.03), CPI (0.00), unemployment (−0.02) and temperature (−0.08) are all close to zero. Day-to-day planning can safely focus on the calendar rather than on economic indicators.
- **Markdowns show only a weak link to sales** (correlation 0.08 where markdown data exists). Markdowns also cluster around holidays, so even that small effect can't be credited to markdowns alone. Their ROI would need a controlled test to prove.
- **Growth is flat.** On the same weeks of the year (weeks 5–43), sales were $1.797B in 2010, $1.786B in 2011 (−0.6%) and $1.831B in 2012 (+2.5%).

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
