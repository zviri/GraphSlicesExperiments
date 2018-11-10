import sys
sys.path.insert(0,'.')
from common import *

from sklearn.cluster import KMeans
import pandas as pd
import argparse
import sys
import json
import numpy as np


if is_jupyter_env():
    import matplotlib.pyplot as plt
    import sys; sys.argv=['', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("ts", help="Time series dataset path", type=str)
parser.add_argument("clusters", help="Clusters output path", type=str)
args = parser.parse_args()

logging.info("Loading datasets...")
ts_df = pd.read_csv(args.ts)

kmeans = KMeans(3)
clusters = kmeans.fit_predict(ts_df)

if is_jupyter_env():
    plt.hist(clusters, 20, log=True);
    plt.title("Cluster histogram")

pd.Series(clusters).to_frame("cluster").to_csv(args.clusters, index=False)
