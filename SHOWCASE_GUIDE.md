# Publish this portfolio on GitHub

The packaging intentionally **does not include** the raw WFP CSV, the full cleaned CSV, the SQL output databases or the full set of derived row-level tables. Download the WFP data yourself before rerunning the pipeline. The already-generated interactive HTML, report PDF, static preview and Power BI model snapshot are included so a reviewer can inspect the portfolio without installing Python.

## Recommended repository first impression

1. Keep `README.md` and `dashboards/dashboard_showcase_preview.png` at their relative locations. The README renders its preview on GitHub.
2. Link `case-study.html`, `showcase/Food_Price_Analysis_Report.pdf`, and `powerbi/README_FIRST.md` in README (already done).
3. A browser's direct `github.com/.../blob/.../interactive_dashboard.html` view shows HTML source, **not the interactive dashboard**. To view it, download and double-click or deploy via GitHub Pages.
4. To use GitHub Pages: **Settings → Pages → Deploy from a branch → main / root**. After deployment, `https://YOUR-USERNAME.github.io/YOUR-REPO/case-study.html` opens the report and `.../dashboards/interactive_dashboard.html` opens the interactive dashboard. Replace placeholders with your own exact repository address.
5. For a real Power BI `.pbix`, open the included PBIP in Power BI Desktop and check each page as described in `powerbi/README_FIRST.md`. Do not label the static HTML screenshot as proof of a validated Desktop report.
6. Confirm the license/attribution terms of the exact WFP/HDX file before redistributing a dataset or its derivatives. Source provenance is in `docs/SOURCE_NOTES.md`.

## Suggested GitHub description

> Bangladesh WFP food-price analytics pipeline: Python cleaning, SQL matched-market analysis, local risk monitoring, data validation, interactive dashboard, Power BI project and an analytical case study.

Suggested repository tags: `data-analysis`, `power-bi`, `sql`, `python`, `portfolio`, `bangladesh`, `food-prices`, `dashboard`, `pandas`.

## Important limitations to show in public

- The source extends to September 2026, but May 2026 is the last comparison month passing the pipeline's documented coverage heuristic.
- Only four markets around Chittagong qualify for the strict fixed-panel risk scores. Never present these as national estimates.
- Different products/units and retail/wholesale are not pooled into a national price index.
- The 2022 source baselines are aggregates and should not be described as measured prices of comparable quality with later actual observations.
- This is an independent analytical portfolio, not official food inflation or a validated prediction of future prices.
