import pandas as pd
import dask.dataframe as dd
import argparse
import unicodedata
import re
from holasek.common import *

if is_jupyter_env():
    import sys; sys.argv=['', 'holasek/data/receivables/', 'data/receivables_cleaned/'];

parser = argparse.ArgumentParser()
parser.add_argument("receivables_path", help="Dataset path", type=str);
parser.add_argument("output_path", help="Output path", type=str);
args = parser.parse_args()

logging.info("Loading receivables dataset...")

receivables_dd = dd.read_csv(args.receivables_path + "*.csv", encoding="utf-8")

def remove_accents(s):
    nkfd_form = unicodedata.normalize('NFKD', s)
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return only_ascii

logging.info("Removing accents...")
receivables_df["content"] = receivables_df["content"].apply(lambda text: remove_accents(text).lower())

logging.info("Saving data to %s", args.output_path)
receivables_df.to_csv(args.output_path, index=False, encoding="utf-8")
