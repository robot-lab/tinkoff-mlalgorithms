import numpy as np

from catboost import CatBoostRegressor

from . import model


class CatBoostModel(model.IModel):

    def __init__(self, **kwargs):
        self.model = CatBoostRegressor()

    def train(self, train_samples, train_labels):
        self.model.fit(train_labels, train_samples)

    def predict(self, samples):
        predicts = []
        for sample in samples:
            prediction = self.model.predict(np.array(sample).reshape(1, -1))[0]
            predicts.append(prediction)
        return predicts
