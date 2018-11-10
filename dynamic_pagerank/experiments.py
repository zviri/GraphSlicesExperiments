from common import *
from experiments_base import Experiment
import numpy as np

from keras.models import Sequential
from keras.layers import Activation, Dense
from keras.optimizers import SGD
from keras.initializers import RandomNormal
import keras


class TFExperiment(Experiment):
    def __init__(self, evaluators, num_epochs):
        self.num_epochs = num_epochs
        super().__init__(evaluators)

    def predict(self, model, X):
        return model.predict(X).T[0].astype(np.float64)

    def fit_model(self, model, X, y):
        model.fit(X, y, epochs=self.num_epochs, batch_size=128, verbose=0)

def build_1layer_perceptron(num_neurons, lr, momentum, l2_regularization=0.0):
    if l2_regularization:
        logging.info("Using L2 regularization: %f", l2_regularization)
    model = Sequential()
    model.add(
        Dense(num_neurons, activation="sigmoid",
              kernel_initializer=RandomNormal(mean=0.0, stddev=0.05, seed=None),
              kernel_regularizer=keras.regularizers.l2(l2_regularization)
    ))
    model.add(Dense(1))
    model.add(Activation("sigmoid"))
    sgd = SGD(lr, momentum=momentum)
    model.compile(loss="mean_squared_error", optimizer=sgd)
    return model

def build_resample_regression_dataset_func(resampler, stepsize=0.1, jitter=False):
    def resample_regression_dataset(X, y):

        Xy = np.column_stack((X, y))
        y_disc = np.digitize(y, np.arange(0, 1, stepsize))

        Xy_resampled, y_resampled = resampler.fit_sample(Xy, y_disc)

        X_new = Xy_resampled[:, 0:-1]
        if jitter:
            logging.info("Using jitter...")
            X_new = X_new + np.random.normal(0, 0.0001, size=X_new.shape)
        y_new = Xy_resampled[:, -1]

        subsample_idx = np.random.randint(X_new.shape[0], size=X.shape[0]) # we want the new dataset to have the same size as the old one
        X_new = X_new[subsample_idx, :]
        y_new = y_new[subsample_idx]

        return (X_new, y_new)
    return resample_regression_dataset
