# Building the Walmart sales dashboard in Tableau Public

Time: about 3–4 hours the first time. Every calculated field can be copied and pasted.

The dashboard answers what a regional sales director asks: **How are we trending? Which stores and departments carry us? Do holidays and markdowns actually pay off?**

## 0. Before you start

1. `python scripts/prepare_data.py` → creates `dashboard/data/` and `dashboard/kpi_check.md`
2. Install **Tableau Public** (free, works on Mac).

## 1. Connect the data

1. Tableau Public → **Text file** → `dashboard/data/store_weekly.csv` (one row per store per week). Most charts use this.
2. Add a second data source → `dept_weekly.csv` (one row per store, department and week), for department charts.
3. Data types: `Date` → Date. `Store` and `Dept` → drag them to **Dimensions** (they're IDs, not numbers to add up).

## 2. Calculated fields (store_weekly)

```
Total Sales
SUM([Weekly Sales])

Weeks
COUNTD([Date])

Avg Weekly Sales (chain)
SUM([Weekly Sales]) / COUNTD([Date])

Sales per Sq Ft
SUM([Weekly Sales]) / SUM([Size])
```

**Like-for-like year over year.** The data runs Feb 2010 to Oct 2012, so full years can't be compared. Compare only the weeks every year has:

```
In Common Weeks
[Week Of Year] >= 6 AND [Week Of Year] <= 43

Sales 2011 (common weeks)
SUM(IF YEAR([Date]) = 2011 AND [In Common Weeks] THEN [Weekly Sales] END)

Sales 2012 (common weeks)
SUM(IF YEAR([Date]) = 2012 AND [In Common Weeks] THEN [Weekly Sales] END)

YoY % (like-for-like)
([Sales 2012 (common weeks)] - [Sales 2011 (common weeks)]) / [Sales 2011 (common weeks)]
```

Use the week range printed as `common_weeks_used` in `kpi_check.md` if it differs from 6–43.

**Holiday lift.** How much bigger is a holiday week than a normal week that year?

```
Normal Week Sales (year)
{ FIXED YEAR([Date]) : SUM(IF NOT [Is Holiday Week] THEN [Weekly Sales] END)
                       / COUNTD(IF NOT [Is Holiday Week] THEN [Date] END) }

Holiday Lift %
(SUM([Weekly Sales]) / COUNTD([Date])) / AVG([Normal Week Sales (year)]) - 1
```

**Markdown effect.** Only from Nov 2011, when markdown data begins:

```
Markdown Period
IF [Markdown Data Available] THEN "Markdown data available" ELSE "No data" END

Markdown Bucket
IF NOT [Markdown Data Available] THEN NULL
ELSEIF [Markdown Total] = 0 THEN "1. None"
ELSEIF [Markdown Total] < 5000 THEN "2. Under $5k"
ELSEIF [Markdown Total] < 20000 THEN "3. $5k-20k"
ELSE "4. $20k+"
END
```

**Store drill-down hierarchy.** In the Data pane, drag `Store` onto `Store Type` and name it **Store Hierarchy**.

## 3. Build the sheets

**KPI tiles (4 sheets).** Total Sales, Avg Weekly Sales (chain), YoY % (like-for-like), Sales per Sq Ft. Large numbers, small labels. Sales in millions (Format → Numbers → Currency (Custom) → Millions).

**Weekly sales trend with holidays.** Columns: `Date` (exact date, continuous). Rows: `Total Sales` as a line. Drag `Holiday` onto **Color** with "None" set to grey, so holiday weeks stand out. **Then add an annotation** on the highest point each December (right-click → Annotate → Point): "Peak week: [date]. The dataset's 'Christmas' flag is the following week." This is the dashboard's signature insight.

**Holiday lift.** Columns: `Holiday` (exclude "None"). Rows: `Holiday Lift %`. Label the bars. Add a zero reference line.

**Store type comparison (dual measure).** Columns: `Store Type`. Rows: `Avg Weekly Sales (chain)` and `Sales per Sq Ft` side by side. This tests whether large stores are better run, or just bigger.

**Top stores (drill-down).** Rows: `Store Hierarchy`. Columns: `Total Sales`. Sort descending, then click **+** on Store Type to drill into stores. Color by `Sales per Sq Ft`, so big-but-inefficient stores are visible.

**Department heatmap (dept_weekly source).** Rows: `Dept`. Columns: `MONTH(Date)`. Color: `SUM(Weekly Sales)`. Filter to the top 20 departments by sales. Shows which departments are seasonal.

**Markdown vs sales.** Columns: `Markdown Bucket`. Rows: `AVG(Weekly Sales)`. Filter `Markdown Data Available` = True. Title it with what you find, for example "Bigger markdowns, barely bigger weeks."

**Economy vs sales (optional).** Scatter: `AVG(Unemployment)` vs `SUM(Weekly Sales)`, one mark per store (`Store` on Detail), with a trend line (Analytics pane). Check R² in the trend line tooltip.

## 4. Assemble the dashboard

Size: **Fixed, 1200 × 1000**.

```
┌───────────────────────────────────────────────────────────────────────┐
│ Walmart Store Sales 2010–2012          [Store Type] [Store] [Holiday] │
├──────────────┬──────────────┬─────────────────┬───────────────────────┤
│ Total sales  │ Avg week     │ YoY (like-for-  │ Sales per sq ft       │
│              │              │ like)           │                       │
├──────────────┴──────────────┴─────────────────┴───────────────────────┤
│ Weekly sales trend, holiday weeks highlighted + peak-week annotation  │
├───────────────────────────────────┬───────────────────────────────────┤
│ Holiday lift %                    │ Store type: size vs efficiency    │
├───────────────────────────────────┼───────────────────────────────────┤
│ Top stores (Type → Store)         │ Markdowns vs sales                │
└───────────────────────────────────┴───────────────────────────────────┘
```

Put the department heatmap on a second dashboard, "Department Seasonality", linked with a navigation button (Objects → Navigation).

1. Filters: `Store Type`, `Store`, `Holiday` → Apply to Worksheets → All using this data source.
2. Filter action: click a store type in the comparison chart → filters every sheet.
3. Titles state the finding, not the chart type.

## 5. Check and publish

1. With filters cleared, compare the KPI tiles with `dashboard/kpi_check.md`.
2. File → **Save to Tableau Public** → "Walmart Store Sales Performance".
3. Add the link and `dashboard/screenshot.png` to the README.

## Interview talking points

- **The Christmas flag is the wrong week.** Walmart's weeks end on Friday, so the flagged week (ending Dec 30/31) is the post-Christmas lull. The real peak is the week before. I checked the flag against the data instead of trusting it.
- **Like-for-like YoY.** Partial years would distort growth, so I compared only weeks present in every year.
- **Size vs efficiency.** Raw sales favor big stores; sales per square foot shows how well each one uses its space.
- **Markdowns are confounded.** Bigger markdowns cluster around holidays, so higher sales in those weeks can't be credited to markdowns alone. Correlation isn't proof.
- **Returns kept in.** Some department-weeks have negative sales (returns). I kept them, because removing them would overstate sales.
