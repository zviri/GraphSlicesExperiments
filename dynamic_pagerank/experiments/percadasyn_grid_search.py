import sys
sys.path.insert(0,'.')
from common import *
from experiments_base import ALL_EVALUATORS
from experiments import TFExperiment, build_1layer_perceptron, build_resample_regression_dataset_func

import pandas as pd
import argparse
import sys
import json
import numpy as np
from imblearn.over_sampling import ADASYN

from hyperopt import fmin, tpe, hp, STATUS_OK, STATUS_FAIL, Trials


if is_jupyter_env():
    import matplotlib.pyplot as plt
    import sys; sys.argv=['', '', '', '', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("dataset", help="Dataset path", type=str);
parser.add_argument("gs_num_trials", help="Num trials for grid search", type=int);
parser.add_argument("gs_training_epochs", help="Number of epochs used for training in on trial", type=int);
parser.add_argument("stepsize", help="Stepsize for discretization", type=float);
parser.add_argument("k_neighbors", help="Number of neighbors for ADASYN", type=int);
parser.add_argument("parameters_path", help="Parameters output", type=str);
parser.add_argument('-j', '--jitter', help="Jitter on/off", action='store_true');
parser.add_argument("--with_l2_regularization", action='store_true', help="Enable L2 regularization")

args = parser.parse_args()

logging.info("Loading dataset...")
dataset_df = pd.read_csv(args.dataset)
adasyn = ADASYN(random_state=0, n_neighbors=args.k_neighbors)
adasyn_resample = build_resample_regression_dataset_func(adasyn, stepsize=args.stepsize, jitter=args.jitter)
class ExperimentData(TFExperiment):
    def load_dataset(self):
        X = dataset_df.drop("year_0", axis=1).values
        y = dataset_df["year_0"].values
        return (X, y)

    def preprocess(self, X, y):
        return adasyn_resample(X, y)

logging.info("Running grid search for learning rate and # of neurons %s(num trials = %d, num_epochs = %d)...",
             "and l2 regularization " if args.with_l2_regularization else "", args.gs_num_trials, args.gs_training_epochs)
def objective(params):
    class OneTimeExperiment(ExperimentData):
        def build_model(self):
            l2_reg = params["l2_reg"] if args.with_l2_regularization else 0.0
            model = build_1layer_perceptron(
                round(params["num_neurons"]), params["learning_rate"], 0.0, l2_reg
            )
            return model
    try:
        expertiment = OneTimeExperiment(ALL_EVALUATORS, args.gs_training_epochs)
        stats = expertiment.run_train_test_validation()
        return {'loss': stats["MSE"], 'status': STATUS_OK }
    except ValueError:
        return {'status': STATUS_FAIL}

space = { "num_neurons": hp.uniform("num_neurons_p", 5, 15),
          "learning_rate": hp.loguniform("learning_rate_p", -7, 0.1)}
if args.with_l2_regularization:
    space["l2_reg"] = hp.loguniform("l2_reg_p", -10, -1)
best_lr_params = fmin(objective, space=space, algo=tpe.suggest, max_evals=args.gs_num_trials, verbose=1)
best_lr_params["num_neurons_p"] = round(best_lr_params["num_neurons_p"])
logging.info("Best number of neurons found: %d", best_lr_params["num_neurons_p"])
logging.info("Best learning rate found: %f", best_lr_params["learning_rate_p"])
if args.with_l2_regularization:
    logging.info("Best l2 regularization parameter found: %f", best_lr_params["l2_reg_p"])
else:
    best_lr_params["l2_reg_p"] = 0.0

logging.info("Running grid search for momentum (num trials = %d, num_epochs = %d)...", args.gs_num_trials, args.gs_training_epochs)
def objective(momentum):
    class OneTimeExperiment(ExperimentData):
        def build_model(self):
            model = build_1layer_perceptron(
                best_lr_params["num_neurons_p"], best_lr_params["learning_rate_p"], momentum, best_lr_params["l2_reg_p"]
            )
            return model
    try:
        expertiment = OneTimeExperiment(ALL_EVALUATORS, args.gs_training_epochs)
        stats = expertiment.run_train_test_validation()
        return {'loss': stats["MSE"], 'status': STATUS_OK }
    except ValueError:
        return {'status': STATUS_FAIL}

best_momentum = fmin(objective, space=hp.loguniform("momentum_p", -7, 0.1),
                     algo=tpe.suggest, max_evals=args.gs_num_trials, verbose=1)
logging.info("Best momentum found: %f", best_momentum["momentum_p"])


logging.info("Saving best parameters to: %s", args.parameters_path)
best_params = {}
best_params.update(best_lr_params)
best_params.update(best_momentum)
json.dump(best_params, open(args.parameters_path, "w"))
