import sys
sys.path.insert(0,'.')
from common import *
from experiments_base import ALL_EVALUATORS
from experiments import TFExperiment, build_1layer_perceptron

import pandas as pd
import argparse
import sys
import json
import numpy as np


if is_jupyter_env():
    import sys; sys.argv=['', '', '', '', '', '', '', ''];

parser = argparse.ArgumentParser()
parser.add_argument("dataset", help="Dataset path", type=str)
parser.add_argument("parameters_path", help="Path to parameters from grid search", type=str)
parser.add_argument("training_epochs", help="Number of epochs used for training in on trial", type=int)
parser.add_argument("num_folds", help="Number of cross validation folds", type=int)
parser.add_argument("model_path", help="Output path for the final model", type=str)
parser.add_argument("cross_val_stats", help="Output path for the cross validation stats", type=str)
parser.add_argument("experiment_description_path", help="Output path for writing experiment description markup", type=str)
args = parser.parse_args()

logging.info("Loading dataset from %s...", args.dataset)
dataset_df = pd.read_csv(args.dataset)

logging.info("Loading parameters from %s...", args.parameters_path)
params = json.load(open(args.parameters_path))
params["num_neurons_p"]=round(params["num_neurons_p"])
experiment_description = """
    Predicting page rank using perceptron with single hidden layer.

    **Evaluation method:** {}-fold cross validation
    **Optimization method:** SGD
    Parameters:
    * num_neurons_p = {} — number of neurons in the hidden layer
    * learning_rate_p = {} — learning rate
    * momentum = {} — momentum
    * l2_reg = {} — L2 regularization""".format(
    args.num_folds, params["num_neurons_p"],
    params["learning_rate_p"], params["momentum_p"], params["l2_reg_p"])

logging.info(experiment_description)

class Experiment(TFExperiment):
    def load_dataset(self):
        X = dataset_df.drop("year_0", axis=1).values
        y = dataset_df["year_0"].values
        return (X, y)

    def build_model(self):
        model = build_1layer_perceptron(
            params["num_neurons_p"], params["learning_rate_p"], params["momentum_p"], params["l2_reg_p"]
        )
        return model

experiment = Experiment(ALL_EVALUATORS, args.training_epochs)
stats_df = experiment.run_cross_validation(args.num_folds)

logging.info("Saving cross validation results to %s", args.cross_val_stats)
stats_df.to_csv(args.cross_val_stats, index=False)

logging.info("Training final model...")
model = experiment.train_final_model()

logging.info("Saving model final model to %s", args.model_path)
model.save(args.model_path)
with open(args.experiment_description_path, 'wt', encoding='utf-8') as o:
    o.write(experiment_description)
