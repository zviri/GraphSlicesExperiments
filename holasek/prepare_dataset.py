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
parser.add_argument("output_folder_path", help="Output folder path", type=str);
args = parser.parse_args()

start_date = dateutil.parser.parse(args.start_date).date()
end_date = dateutil.parser.parse(args.end_date).date()

logging.info("Loading receivables between %s and %s from db...", args.start_date, args.end_date)
delta = timedelta(days=30)
start_date_iter = start_date
end_date_iter = start_date + delta
iter = 0
while start_date_iter <= end_date:
    logging.info("\tQuerying range %s - %s", start_date_iter, end_date_iter)
    files_df = sql2df("SELECT * FROM file_tab WHERE file_type_id =530 "\
                      "AND publish_date >= %(START_DATE)s AND publish_date <= %(END_DATE)s ",
                      {"START_DATE": start_date_iter, "END_DATE": end_date_iter})

    output_path = args.output_folder_path + "/receivables_{}.csv".format(iter)
    logging.info("\tSaving data to %s", output_path)
    files_df.to_csv(output_path, index=False, encoding="utf-8")
    start_date_iter = end_date_iter + timedelta(days=1)
    end_date_iter += delta
    iter += 1
