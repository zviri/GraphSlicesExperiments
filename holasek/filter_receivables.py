import pandas as pd
import argparse
from common import *

if is_jupyter_env():
    import sys; sys.argv=['', 'holasek/data/extracted_data.csv', 'holasek/data/creditors.csv', 'holasek/data/filtered_receivables.csv'];

parser = argparse.ArgumentParser()
parser.add_argument("receivables", help="Extracted receivables file", type=str);
parser.add_argument("creditors", help="Creditors list", type=str);
parser.add_argument("output", help="Filtered receivables", type=str);
args = parser.parse_args()

logging.info("Loading receivables from: %s", args.receivables)
receivables_df = pd.read_csv(args.receivables, encoding="utf-8")

logging.info("Loading creditors from: %s", args.creditors)
creditors_df = pd.read_csv(args.creditors, encoding="utf-8")

filtered_receivables_df = receivables_df.merge(creditors_df[["creditor_string_id"]],
                     left_on="creditor_string_id", right_on="creditor_string_id")

logging.info("Saving filtered receivables to: %s", args.output)
filtered_receivables_df.to_csv(args.output, encoding="utf-8", index=False)
