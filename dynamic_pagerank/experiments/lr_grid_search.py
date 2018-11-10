import sys
sys.path.insert(0,'.')
from common import *
from experiments_base import ALL_EVALUATORS, Experiment

from sklearn import linear_model
import pandas as pd
import argparse
import sys
import json
import numpy as np

from hyperopt import fmin, tpe, hp, STATUS_OK, STATUS_FAIL, Trials

if is_jupyter_env():
    import sys; sys.argv=['', '', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("dataset", help="Dataset path", type=str)
parser.add_argument("gs_num_trials", help="Num trials for grid search", type=int)
parser.add_argument("parameters_path", help="Parameters output", type=str)
args = parser.parse_args()

logging.info("Loading dataset...")
dataset_df = pd.read_csv(args.dataset)
class ExperimentData(Experiment):
    def load_dataset(self):
        X = dataset_df.drop("year_0", axis=1).values
        y = dataset_df["year_0"].values
        return (X, y)

logging.info("Running grid search for alpha (num trials = %d)...", args.gs_num_trials)
def objective(alpha):
    class OneTimeExperiment(ExperimentData):
        def build_model(self):
            model = linear_model.Ridge(alpha)
            return model
    expertiment = OneTimeExperiment(ALL_EVALUATORS)
    stats = expertiment.run_train_test_validation()
    return {'loss': stats["MSE"], 'status': STATUS_OK }

best_alpha= fmin(objective, space=hp.loguniform("alpha_p", -7, 0.1),
                 algo=tpe.suggest, max_evals=args.gs_num_trials, verbose=1)
logging.info("Best alpha found: %f", best_alpha["alpha_p"])

logging.info("Saving best parameters to: %s", args.parameters_path)
json.dump(best_alpha, open(args.parameters_path, "w"))
