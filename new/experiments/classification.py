import sys
sys.path.insert(0,'.')
from common import *

from sklearn.externals import joblib
from sklearn.svm import LinearSVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import cross_validate
import pandas as pd
import argparse
import sys
import json
import numpy as np


if is_jupyter_env():
    import matplotlib.pyplot as plt
    import sys; sys.argv=['', 'data/datasets/ts_4.csv', 'data/datasets/kmeansclusters_4.csv', '5', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("ts", help="Time series dataset input path", type=str)
parser.add_argument("clusters", help="Clusters input path", type=str)
parser.add_argument("folds", help="Number of cross val folds", type=int)
parser.add_argument("model", help="Clusters output path", type=str)
parser.add_argument("cross_val_stats", help="Cross val stats output path", type=str)
args = parser.parse_args()

logging.info("Loading datasets...")
ts_df = pd.read_csv(args.ts)
clusters_df = pd.read_csv(args.clusters)
dataset_df = pd.concat([ts_df, clusters_df], axis=1)

logging.info("Running cross validation (k=%d)...", args.folds)
clf = OneVsRestClassifier(LinearSVC(class_weight="balanced", C=0.001))
scores = cross_validate(clf, ts_df, clusters_df["cluster"], cv=args.folds, scoring=("precision_macro", "recall_macro", "f1_macro"))
cv_stats = {"f1_score": scores["test_f1_macro"].mean(),
            "precision": scores["test_precision_macro"].mean(),
            "recall": scores["test_recall_macro"].mean()}


logging.info("Fitting final model...")
clf.fit(ts_df, clusters_df["cluster"])

logging.info("Saving results...")
json.dump(cv_stats, open(args.cross_val_stats, "w"))
joblib.dump(clf, args.model)
