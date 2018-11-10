import pandas as pd
import json
import numpy as np
import argparse
from itertools import tee
from common import *

if is_jupyter_env():
    import sys; sys.argv=['', '', '', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("yearly_dataset_path", help="Yearly dataset path in jsonline format.", type=str)
parser.add_argument("window_size", help="Window size for the time series.", type=int)
parser.add_argument("ts_output_path", help="Timeseries dataset output path.", type=str)
parser.add_argument("insdata_output_path", help="Insolvency dataset output path.", type=str)
args = parser.parse_args()

window_size = args.window_size

# Loading dataset to memory
logging.info("Loading dataset from: %s", args.yearly_dataset_path)
yearly_prs = []
insolvency_data = []
for line in open(args.yearly_dataset_path):
    record = json.loads(line)
    yearly_prs += [dict(record["pr"])]
    insolvency_data += [{"id": record["id"], "stringId": record["stringId"], "nodeType": record["nodeType"]}]
yearly_prs_df = pd.DataFrame(yearly_prs)
insolvency_data_df = pd.DataFrame(insolvency_data)
assert yearly_prs_df.shape[0] == insolvency_data_df.shape[0]

# Data set generation

def rolling_window(iterable, window):
    iters = tee(iterable, window)
    for i in range(1, window):
        for each in iters[i:]:
            next(each, None)
    return map(list, zip(*iters))

logging.info("Generating time series dataset using window size: %d", args.window_size)
dataset_df = pd.DataFrame()
dataset_insdata_df = pd.DataFrame()
for window in rolling_window(yearly_prs_df.columns, window_size):
    features = yearly_prs_df[window[:window_size - 1]]
    features.columns = np.array(
        list(map(lambda idx: "year_{}".format(idx), reversed(range(1, len(window[:-1]) + 1))))
    )

    pred = yearly_prs_df[[window[-1]]]
    pred.columns = np.array(["year_0"])
    dataset_df = dataset_df.append(pd.concat([features, pred], axis=1))
    dataset_insdata_df = dataset_insdata_df.append(insolvency_data_df)

assert dataset_insdata_df.shape[0] == dataset_df.shape[0]

logging.info("Writing timeseries dataset to: %s", args.ts_output_path)
dataset_df.to_csv(args.ts_output_path, index=False)

logging.info("Writing insolvency data dataset to: %s", args.insdata_output_path)
dataset_insdata_df.to_csv(args.insdata_output_path, index=False)
