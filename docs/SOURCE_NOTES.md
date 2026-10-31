# Source and provenance

- Input: `data/raw/wfp_food_prices_bgd.csv`, file as received on 2026-10-26.
- Described source: WFP Bangladesh Food Prices on HDX.
- Original upload is preserved unchanged; the pipeline does not download or scrape data.
- SHA-256 of the supplied bytes: `b003cd22f0884c47d7b8c4527041ede4920b59da4dc0d1e4b31b10be4dd03765`.
- Dataset page supplied in project setup: https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh
- Exact resource download URL and original download date: not supplied.
- Source licence: other WFP country datasets on HDX list CC BY-IGO; confirm on the Bangladesh dataset page, record it here, and attribute WFP/HDX.
- Source aggregation method: not established from the CSV labels alone. Flags are retained and profiled.

Git ignores raw CSVs by default, so the published repository does not redistribute the source file.

Current observed counts, dates, inventory and source flags are produced by scripts/profile_data.py in docs/PROFILING_REPORT.md and outputs/tables/source_*.csv. Cleaning decisions are recorded separately; the invalid historical date remains visible in the raw profile and rejected-row audit.
