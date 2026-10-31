# Power BI Desktop: Open the generated project

**What is supplied:** An editable Power BI Project (`.pbip`) containing generated Power BI enhanced report definitions (PBIR), a tabular model (`model.bim`) and **embedded real-data snapshot tables**. The native project has four report pages and source-snapshot visuals. A complete `PBIX` binary is **not** provided. The native project has not been opened or rendered inside Windows Power BI Desktop during this build; treat the PBIP as a candidate that needs your first in-Desktop verification.

## Quick start — Windows

1. Extract the entire project ZIP first; do not open anything inside compressed ZIP view.
2. Install or open **Power BI Desktop** (a reasonably recent release supporting Power BI Projects and PBIR).
3. Navigate to `powerbi` inside the extracted project folder.
4. Double-click `Bangladesh_Food_Price_Intelligence.pbip`.
5. Allow Desktop to load the semantic model. If asked about model edits or preview behavior, follow the Power BI project prompts.
6. **Check every visual and all four pages.** If Power BI reports a compatibility error, use the dependable manual guide at `../dashboards/POWERBI_GUIDE.md` and import the regenerated CSVs after running `run_all.bat`; this source export has not been Desktop-tested.
7. In Power BI Desktop, click **File → Save As → Power BI Desktop file (.pbix)** to create your actual `.pbix` after visual checks.
8. Once the `.pbix` is created, add screenshots of your actual Power BI report (not the HTML dashboard) to your GitHub README.

## Report pages

| Page | Visuals | Correct interpretation |
| --- | --- | --- |
| Executive Risk Overview | Eligible-series KPI, highest-score KPI, risk-ranked bar chart | Strict 12-month four-market **local** risk scores |
| Commodity Price Explorer | Green chili fixed-panel 12-month line | Same series, same markets, BDT/kg; not CPI |
| Market Moves and Staples | May 2026 MoM ranking and 2022 staple change | Matched markets, distinct comparison cohorts |
| Coverage and Methods | Reported distinct series and markets by month | Coverage varies; low months are not used for the risk snapshot |

## About snapshot updates

The Power BI model embeds a **static** curated snapshot in its Power Query M partitions. It does **not** connect to the raw WFP file or refresh automatically from source. To update the embedded model after downloading a later WFP CSV, run the main pipeline and then `python -m scripts.build_powerbi_project` **while Power BI Desktop is closed**, then reopen the `.pbip`. To build a live CSV-linked model instead, use the original detailed [`POWERBI_GUIDE.md`](../dashboards/POWERBI_GUIDE.md), which also includes explicit relationships and DAX measures.

## Important analytics constraints

The risk score is an index, not a probability. The panel covers four markets around Chittagong. Scores are not nationwide. The July–September 2026 source observations do not justify updating May 2026 risk rankings under the current coverage heuristic. Commodity/unit/pricetype are separate series, and 2022 baseline comparisons retain aggregate-source caveats.

**Desktop compatibility disclaimer:** `.pbip`/PBIR are text-based editable Power BI authoring formats, not image mockups. All included JSON has been syntactically checked, but Desktop rendering cannot be guaranteed from this environment. Microsoft documentation: https://learn.microsoft.com/power-bi/developer/projects/projects-overview
