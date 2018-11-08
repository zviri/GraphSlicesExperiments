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
parser.add_argument("receivables_clean_path", help="Clea path", type=str);
parser.add_argument("output_path", help="Output path", type=str);
args = parser.parse_args()


def deputy_type(row):
    if row["is_deputy"] == True:
        content = re.sub(r'\s+', '', row["content"])
        if "druhzastupce:obecnyzmocnenec" in content:
            return "Obecný zmocněnec"
        elif "druhzastupce:pravnizastupce" in content:
            return "Právní zástupce"
        elif "druhzastupce:opatrovnikpodleprocesnihoprava" in content:
            return "Opatrovník podle procesního práva"
        elif "druhzastupce:zakonnyzastupce" in content:
            return "Zákonný zástupce"
        elif "druhzastupce:jinydruhzastupce" in content:
            return "Jiný druh zástupce"
        else:
            return None
    else:
        return None

def extract_name(row):
    if row["is_deputy"] == True:
        content = re.sub(r'[ \r]+', '', row["content"])
        content = content[content.index("overitel#zastupce"):]
        name_search = re.search('fyzickaprijmeni\:(.*)jmeno:(.*)', content)
        if name_search is None:
            return None
        last_name = name_search.group(1)
        first_name = name_search.group(2)
        return " ".join([first_name, last_name]).title()
    else:
        return None

def process_df(df):
    df["is_deputy"] = df["content"].apply(lambda s: "overitel#zastupce" in re.sub(r'\s+', '', s))
    df["is_not_deputy"] = df["content"].apply(lambda s: "#veritelozastupce" in re.sub(r'\s+', '', s))
    df["deputy_type"] = df.apply(deputy_type, axis=1)
    df["deputy_name"] = df.apply(extract_name, axis=1)
    df = df.drop(["content"], axis=1)
    return df

logging.info("Extracting deputies...")
receivables_df = dd\
.read_parquet(args.receivables_clean_path + "*.parquet")\
.map_partitions(process_df)\
.compute(num_workers=N_CORES, scheduler='processes')

receivables_df = receivables_df[["insolvency_id", "publish_date", "creditor", "creditor_string_id",
                "is_deputy", "is_not_deputy", "deputy_type", "deputy_name", "url"]]
receivables_df.to_csv(args.output_path, index=False, encoding="utf-8")
