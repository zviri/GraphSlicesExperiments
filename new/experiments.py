from common import *
from experiments_base import Experiment
import numpy as np

from keras.models import Sequential
from keras.layers import Activation, Dense
from keras.optimizers import SGD
from keras.initializers import RandomNormal

class TFExperiment(Experiment):
    def __init__(self, evaluators, num_epochs):
        self.num_epochs = num_epochs
        super().__init__(evaluators)

    def predict(self, model, X):
        return model.predict(X).T[0].astype(np.float64)

    def fit_model(self, model, X, y):
        model.fit(X, y, epochs=self.num_epochs, batch_size=128, verbose=0)

def build_1layer_perceptron(num_neurons, lr, momentum):
    model = Sequential()
    model.add(
        Dense(num_neurons, activation="sigmoid",
              kernel_initializer=RandomNormal(mean=0.0, stddev=0.05, seed=None)
    ))
    model.add(Dense(1))
    model.add(Activation("sigmoid"))
    sgd = SGD(lr, momentum=momentum)
    model.compile(loss="mean_squared_error", optimizer=sgd)
    return model
