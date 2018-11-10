import pandas as pd
import numpy as np
import argparse
from common import *
from sklearn.preprocessing import MinMaxScaler, LabelBinarizer


if is_jupyter_env():
    import matplotlib.pyplot as plt
    import sys; sys.argv=['', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("ts_dataset", help="Time series dataset", type=str);
parser.add_argument("output", help="Transformed output dataset path.", type=str);
args = parser.parse_args()

logging.info("Loading dataset: %s", args.ts_dataset)
dataset_df = pd.read_csv(args.ts_dataset)

if is_jupyter_env():
    plt.hist(dataset_df["year_0"], 20, log=True);
    plt.title("Histogram of raw values")

logging.info("Applying MinMax scaling...")
scaler = MinMaxScaler(feature_range=(-1, 1))
dataset_rescaled = scaler.fit_transform(dataset_df)

if is_jupyter_env():
    plt.hist(dataset_rescaled[:,-1], 20, log=True);
    plt.title("Histogram of values after (-1,1) rescaling")


logging.info("Applying sigmoid transformation...")
apply_sigmoid_func = np.vectorize(lambda x: 1 / (1 + np.exp(-4 * x)))
dataset_sigm = apply_sigmoid_func(dataset_rescaled)

if is_jupyter_env():
    _ = plt.hist(dataset_sigm_df[:,-1], 20, log=True)
    plt.title("Histogram of values after applying the sigmoid function")

logging.info("Writing transformed dataset to: %s", args.output)
dataset_sigm_df = pd.DataFrame(dataset_sigm, columns=dataset_df.columns)
dataset_sigm_df.to_csv(args.output, index=False)
