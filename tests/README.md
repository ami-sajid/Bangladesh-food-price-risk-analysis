# Test data only

All records in sample_test_only.csv and test_analysis.py are fabricated for software checks. They are not observations from WFP and must never be used as findings, dashboard screenshots or CV numbers.

Run `python -m pytest -q` from the project root. Tests use a temporary SQLite database, check calendar gaps, missing columns, HXL detection, custom mappings, unit separation, invalid values, retained outliers and repeatable loading. They do not contact PostgreSQL or overwrite real outputs.

Revision 2 adds regression cases for the invalid date, non-food preservation, market-entry composition bias, the YoY history gate, fixed-panel risk and the 2024 cutoff. The full pipeline also independently reconciles real SQL outputs from cleaned records.
