import pandas as pd
from db import sql2df
import argparse
from common import *
import dateutil.parser
from datetime import timedelta, date

if is_jupyter_env():
    import sys; sys.argv=['', '', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("start_date", help="ISO Format 2014-07-01", type=str);
parser.add_argument("end_date", help="ISO Format 2014-07-01", type=str);
parser.add_argument("N", help="Top N creditors", type=int);
parser.add_argument("output", help="Output path for list of most frequent creditors", type=str);
args = parser.parse_args()

start_date = dateutil.parser.parse(args.start_date).date()
end_date = dateutil.parser.parse(args.end_date).date()

logging.info("Extracting N=%d most frequent creditors between %s and %s from db...", args.N, args.start_date, args.end_date)

creditors_df = sql2df("SELECT creditor_string_id, count(*) as count FROM file_tab "\
                  "WHERE file_type_id =530 AND publish_date >= %(START_DATE)s AND publish_date <= %(END_DATE)s "\
                  "GROUP BY creditor_string_id ORDER BY count DESC LIMIT %(N)s",
                  {"START_DATE": start_date, "END_DATE": end_date, "N": args.N})


creditors_df.to_csv(args.output, encoding="utf-8", index=False)
