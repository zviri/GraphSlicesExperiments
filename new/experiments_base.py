from abc import ABC, abstractmethod
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import tensorflow as tf
from keras.losses import binary_crossentropy
import pandas as pd
from common import *

class Evaluator(ABC):
    def __init__(self):
        super(Evaluator, self).__init__()

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def evaluate(self, pred_y, real_y):
        pass

class MSEEvaluator(Evaluator):
    def get_name(self):
        return "MSE"

    def evaluate(self, pred_y, real_y):
        return mean_squared_error(real_y, pred_y)

class MAEEvaluator(Evaluator):
    def get_name(self):
        return "MAE"

    def evaluate(self, pred_y, real_y):
        return mean_absolute_error(real_y, pred_y)

class R2Evaluator(Evaluator):
    def get_name(self):
        return "R2"

    def evaluate(self, pred_y, real_y):
        return r2_score(real_y, pred_y)

class CrossEntropyEvaluator(Evaluator):
    def get_name(self):
        return "CrossEntropy"

    def evaluate(self, pred_y, real_y):
        eval_tf = binary_crossentropy(tf.convert_to_tensor(real_y), tf.convert_to_tensor(pred_y))
        ce = tf.Session().run(eval_tf).mean()
        return ce

ALL_EVALUATORS = [MSEEvaluator(), MAEEvaluator(), R2Evaluator(), CrossEntropyEvaluator()]

class Experiment(ABC):
    def __init__(self, evaluators):
        self.evaluators = evaluators
        super(Experiment, self).__init__()

    @abstractmethod
    def load_dataset(self):
        pass # return (X, y)

    @abstractmethod
    def build_model(self):
        pass

    def fit_model(self, model, X, y):
        model.fit(X, y)

    def predict(self, model, X):
        return model.predict(X)

    def preprocess(self, X, y):
        return (X, y)

    def run_cross_validation(self, k=5):
        X, y = self.load_dataset()
        kf = KFold(n_splits=5)
        stats_df = pd.DataFrame()
        logging.info("Running cross validation with K=%d", k)
        for split_idx, (train, test) in enumerate(kf.split(X)):
            logging.info("\tRunning split %d", split_idx + 1)
            train_X, train_y = X[train], y[train]
            test_X, test_y = X[test], y[test]

            model = self.build_model()
            train_X, train_y = self.preprocess(train_X, train_y)
            self.fit_model(model, train_X, train_y)
            pred_y = self.predict(model, test_X)

            stats = [(eval.get_name(), eval.evaluate(pred_y, test_y)) for eval in self.evaluators]
            stats_df = stats_df.append(pd.DataFrame([dict(stats)]), ignore_index=True)
        return stats_df

    def run_train_test_validation(self, test_size=0.1):
        X, y = self.load_dataset()
        train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=test_size)
        model = self.build_model()
        train_X, train_y = self.preprocess(train_X, train_y)
        self.fit_model(model, train_X, train_y)
        pred_y = self.predict(model, test_X)
        stats = [(eval.get_name(), eval.evaluate(pred_y, test_y)) for eval in self.evaluators]
        return dict(stats)

    def train_final_model(self):
        X, y = self.load_dataset()
        model = self.build_model()
        X, y = self.preprocess(X, y)
        self.fit_model(model, X, y)
        return model
