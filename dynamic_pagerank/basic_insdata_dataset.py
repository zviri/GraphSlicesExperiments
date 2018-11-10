import pandas as pd
import numpy as np
import argparse
from common import *
from sklearn.preprocessing import LabelBinarizer

if is_jupyter_env():
    import sys; sys.argv=['', '', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("ts_dataset", help="Time series dataset path.", type=str);
parser.add_argument("insdata", help="Insolvency data corresping to the time series dataset.", type=str);
parser.add_argument("basic_insdata_dataset", help="Output dataset.", type=str);
args = parser.parse_args()

logging.info("Loading datasets...")
ts_dataset_df = pd.read_csv(args.ts_dataset)
insdata_df = pd.read_csv(args.insdata)
assert ts_dataset_df.shape[0] == insdata_df.shape[0]

logging.info("Binarizing nodeType...")
lb = LabelBinarizer()
node_type_f = lb.fit_transform(insdata_df.nodeType)
node_type_f_df = pd.DataFrame(node_type_f, columns=lb.classes_)

output_dataset_df = pd.concat((ts_dataset_df, node_type_f_df), axis=1)

logging.info("Writing output...")
output_dataset_df.to_csv(args.basic_insdata_dataset, index=False)
