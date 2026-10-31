"""Change source column names here; the rest of the project uses canonical names."""
from pathlib import Path
import os
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
COLUMN_MAP = {
    'date': 'date', 'division': 'admin1', 'district': 'admin2',
    'market': 'market', 'latitude': 'latitude', 'longitude': 'longitude',
    'category': 'category', 'commodity': 'commodity', 'unit': 'unit',
    'priceflag': 'priceflag', 'pricetype': 'pricetype', 'currency': 'currency',
    'price': 'price', 'usdprice': 'usdprice',
    'source_market_id': 'market_id', 'source_commodity_id': 'commodity_id',
}
REQUIRED_COLUMNS = ['date', 'division', 'market', 'commodity', 'unit',
                    'pricetype', 'currency', 'price']
# ISO dates are preferred. Set DATE_FORMAT='%d/%m/%Y' for explicit day-first dates.
DATE_FORMAT = None
CSV_ENCODING = 'utf-8-sig'
CSV_SEPARATOR = ','
BDT_ALIASES = {'bdt', 'taka', 'bangladeshi taka', 'tk'}
# Explicit name corrections only. Do not silently merge distinct grades or units.
NAME_ALIASES = {'division': {}, 'district': {}, 'market': {}, 'commodity': {},
                'unit': {}, 'pricetype': {}}
MIN_RISK_MONTHS = 12  # Fixed twelve-calendar-month panel; must remain 12.
VOLATILITY_CAP = 0.30  # 30% CV saturates the volatility component.
RECENT_CHANGE_CAP = 0.20  # 20% positive MoM saturates the increase component.
VOLATILITY_WEIGHT = 0.60
OUTLIER_IQR_MULTIPLIER = 3.0
DB_BACKEND = os.getenv('DB_BACKEND', 'auto').strip().lower()
RAW_FILE = os.getenv('RAW_FILE', '').strip()

# Dataset-specific audit rules; source remains unchanged.
MIN_VALID_DATE = '1998-01-01'
RISK_START = '2024-01-01'
CORE_STAPLES = ['rice', 'wheat flour', 'oil (palm)', 'oil (soybean', 'lentils']
MIN_LONG_HISTORY_MONTHS = 60
NON_FOOD_CATEGORIES = {'non-food'}
# Unknown categories are not silently classified as food.
FOOD_CATEGORIES = {'cereals and tubers', 'vegetables and fruits', 'oil and fats',
                   'pulses and nuts', 'meat, fish and eggs', 'miscellaneous food', 'milk and dairy'}
# Broad-coverage cutoff: latest month with at least this fraction of the trailing
# twelve-month maximum food-series count AND maximum market count (retail only).
COVERAGE_FRACTION = 0.50
ANALYSIS_MONTH = None  # Optional explicit YYYY-MM-01 override, disclosed in reports.
