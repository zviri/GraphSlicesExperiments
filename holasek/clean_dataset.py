import pandas as pd
import dask.dataframe as dd
import argparse
import unicodedata
import re
from common import *
import re

if is_jupyter_env():
    import sys; sys.argv=['', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("receivables_path", help="Dataset path", type=str);
parser.add_argument("output_path", help="Output path", type=str);
args = parser.parse_args()

def remove_accents(s):
    nkfd_form = unicodedata.normalize('NFKD', s)
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return only_ascii

def preprocess_df(df):
    df["content"] = df["content"].fillna("")
    df["content"] = df["content"].apply(
        lambda content: remove_accents(re.sub(r"[©@]", "#", content)).lower().decode("utf-8") # need to special characters later
    )
    return df

logging.info("Removing accents...")
receivables_dd = dd\
.read_parquet(args.receivables_path + "*.parquet")\
.map_partitions(preprocess_df)\
.to_parquet(args.output_path, compression="gzip")
