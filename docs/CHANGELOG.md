# Revision 3: dashboard and publication cleanup

- Adds `scripts/build_dashboard.py`: single-file HTML dashboard (inline SVG) built from `outputs/tables`, wired into `run_all.py`.
- Dashboard hides year-over-year points built on fewer than 10 matched markets and ends the staple trend at the last month where all four staples are well covered.
- README rewritten for publication: key findings, limitations and data licence note up front.
- Career-prep documents removed from the repository.

# Revision 2: real-data correction

- Raw uploaded CSV included unchanged; completed outputs now accompany the source code.
- Quarantines dates before the verified release range, including the reported 1900 record, with an explicit quality flag and reason.
- Classifies food versus non-food/unknown categories. Non-food stays auditable but cannot enter food rankings.
- Adds source IDs, year/month coverage, source inventory and source-flag profiles.
- Selects and discloses a broad-coverage comparison month separately from the latest source month.
- Replaces changing-market temporal averages with matched MoM/YoY endpoints and matched 2022 baselines.
- Requires twelve observed months for each market-series entering a YoY comparison.
- Uses identical markets across all twelve risk-window months; the window cannot begin before 2024.
- Limits pre-2024 long-run plots to configured core staples with at least sixty same-market observations.
- Exports panel membership and monthly score inputs, highlights geographic concentration and preserves score ties.
- Updates charts, dashboard models/DAX, findings, limitations and interview explanations.

The old all-market temporal averaging approach must not be used to interpret this release's changing coverage.
