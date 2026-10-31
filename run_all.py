"""One entry point. Run from any working directory; no credentials are logged."""
import sys
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    try:
        import config as C
        from scripts.common import setup_logging, get_engine, ProjectError
        from scripts import profile_data,clean_data,load_to_db,run_analysis,make_charts,build_dashboard,generate_report,validate_outputs
    except ImportError as error:
        print('A Python dependency is missing. Double-click run_all.bat or run: python -m pip install -r requirements.txt')
        print('Missing module:',error.name)
        return 1
    setup_logging()
    status=ROOT/'outputs/run_status.json'
    status.write_text(json.dumps({'status':'running','started_utc':datetime.now(timezone.utc).isoformat()}))
    engine=None
    try:
        for label,action in [('1/6 Profile source',profile_data.run),('2/6 Clean data',clean_data.run)]:
            logging.info(label);action()
        engine=get_engine()
        logging.info('3/6 Load star schema');load_to_db.run(engine)
        logging.info('4/6 Execute all SQL analyses');run_analysis.run(engine)
        logging.info('Independently reconcile SQL results');validate_outputs.run()
        logging.info('5/6 Render six charts');make_charts.run()
        logging.info('Build HTML dashboard');build_dashboard.run()
        logging.info('6/6 Generate findings and README');generate_report.run()
        status.write_text(json.dumps({'status':'success','backend':engine.dialect.name,
                                      'finished_utc':datetime.now(timezone.utc).isoformat()},indent=2))
        logging.info('SUCCESS. Open docs/FINDINGS.md, outputs/tables and outputs/charts.')
        return 0
    except ProjectError as error:
        message=str(error)
    except Exception as error:
        # Never print database URLs or exception bodies that may include passwords.
        message=f'{type(error).__name__}: pipeline could not finish. Check CSV formatting, file locks, dependencies and database settings.'
    finally:
        if engine is not None: engine.dispose()
    status.write_text(json.dumps({'status':'failed','message':message},indent=2))
    logging.error('%s Previous exports may be stale; only trust a SUCCESS run.',message)
    return 1

if __name__=='__main__':
    sys.exit(main())
