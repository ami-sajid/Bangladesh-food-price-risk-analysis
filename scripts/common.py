"""Shared CSV, logging and database helpers."""
import csv
import hashlib
import logging
import math
import os
import pandas as pd
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import URL
import config as C

class ProjectError(Exception):
    """A problem the user can fix without reading a traceback."""

def setup_logging():
    (C.ROOT / 'outputs').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(
                            C.ROOT / 'outputs/pipeline.log', encoding='utf-8')], force=True)

def read_raw(path=None):
    if path is None:
        files = sorted((C.ROOT / 'data/raw').glob('*.csv'))
        if C.RAW_FILE:
            files = [C.ROOT / 'data/raw' / C.RAW_FILE]
        if len(files) != 1 or not files[0].is_file():
            raise ProjectError('Put exactly one WFP CSV in data/raw, or set RAW_FILE in .env.')
        path = files[0]
    with open(path, encoding=C.CSV_ENCODING, newline='') as handle:
        rows = list(csv.reader(handle, delimiter=C.CSV_SEPARATOR))
    if not rows:
        raise ProjectError('The CSV is empty. Download the actual CSV, not an HTML page.')
    headers = [v.strip().lstrip('\ufeff').lower() for v in rows[0]]
    if len(set(headers)) != len(headers):
        raise ProjectError('CSV headers repeat after trimming. Give each column a unique name.')
    # Detect metadata by tag content, wherever it occurs after the header.
    tagged = [i for i, row in enumerate(rows[1:], 1)
              if any(v.strip().lower().startswith('#date') for v in row)
              or sum(v.strip().startswith('#') for v in row) >= max(2, len(headers)//2)]
    records = [row for i, row in enumerate(rows[1:], 1) if i not in tagged and any(v.strip() for v in row)]
    if any(len(row) != len(headers) for row in records):
        raise ProjectError('CSV row width differs from its header. Check CSV_SEPARATOR in config.py.')
    df = pd.DataFrame(records, columns=headers).replace(r'^\s*$', pd.NA, regex=True)
    mapped = {str(source).strip().lower(): canonical for canonical, source in C.COLUMN_MAP.items()
              if source is not None}
    if len(mapped) != sum(v is not None for v in C.COLUMN_MAP.values()):
        raise ProjectError('COLUMN_MAP maps a source column more than once. Use unique source names.')
    df = df.rename(columns=mapped)
    missing = [k for k in C.REQUIRED_COLUMNS if k not in df.columns]
    if missing:
        raise ProjectError('Missing required columns: '+', '.join(missing)+
                           '. Edit COLUMN_MAP in config.py. Available source headers: '+', '.join(headers))
    for k in C.COLUMN_MAP:
        if k not in df:
            df[k] = pd.NA
    return df, {'source': str(path.name), 'hxl_rows_skipped': len(tagged), 'headers': headers,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def parse_dates(series):
    # Reject ambiguous slash dates unless the user specifies a format.
    if C.DATE_FORMAT is None and series.dropna().astype(str).str.contains(r'^\d{1,2}/\d{1,2}/').any():
        raise ProjectError('Slash dates are ambiguous. Set DATE_FORMAT in config.py, e.g. %d/%m/%Y.')
    return pd.to_datetime(series, format=C.DATE_FORMAT or 'mixed', errors='coerce')

def sqlite_engine():
    engine = create_engine('sqlite:///'+str(C.ROOT/'outputs/food_prices.db'))
    @event.listens_for(engine, 'connect')
    def configure(dbapi_connection, record):
        dbapi_connection.execute('PRAGMA foreign_keys=ON')
        dbapi_connection.create_function('SQRT', 1, lambda x: math.sqrt(max(x, 0)) if x is not None else None)
    return engine

def get_engine():
    if C.DB_BACKEND not in {'postgres', 'sqlite', 'auto'}:
        raise ProjectError('DB_BACKEND must be postgres, sqlite or auto.')
    if C.DB_BACKEND == 'sqlite':
        return sqlite_engine()
    url = URL.create('postgresql+psycopg2', username=os.getenv('PGUSER','postgres'),
                     password=os.getenv('PGPASSWORD',''), host=os.getenv('PGHOST','localhost'),
                     port=int(os.getenv('PGPORT','5432')), database=os.getenv('PGDATABASE','food_prices'))
    engine = create_engine(url, connect_args={'connect_timeout': 4})
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return engine
    except Exception:
        engine.dispose()
        if C.DB_BACKEND == 'postgres':
            raise ProjectError('Cannot connect to PostgreSQL. Check the service, database and .env. '
                               'Use DB_BACKEND=sqlite to run without PostgreSQL.') from None
        logging.warning('PostgreSQL unavailable: AUTO fallback to outputs/food_prices.db (SQLite).')
        return sqlite_engine()

def markdown_table(df, limit=10):
    if df.empty:
        return '_No eligible observations._'
    def fmt(v):
        if pd.isna(v): return 'N/A'
        if isinstance(v, float): return f'{v:,.2f}'
        return str(v).replace('|', '/').replace('\n', ' ')
    header='| '+' | '.join(df.columns)+' |'
    divider='| '+' | '.join(['---']*len(df.columns))+' |'
    return '\n'.join([header,divider]+['| '+' | '.join(fmt(v) for v in row)+' |'
                                       for row in df.head(limit).itertuples(index=False,name=None)])
