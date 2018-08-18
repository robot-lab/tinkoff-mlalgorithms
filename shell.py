import json
import logger
import pickle
import tester

import numpy as np
import pandas as pd

import models.linear_model as lm
import models.k_nearest_neighbors as knn
import models.random_forest as rf

import parsers.linear_model_parser as lmp


@logger.decor_class_logging_error_and_time(
    "__init__", "__input", "output", "predict", "test", "save_model"
)
class Shell:

    def __init__(self, config_filename="ml_config.json",
                 parser_instance=None, model_instance=None):
        """
        Constructor which initialize class fields.
        """
        self.__validation_labels = None
        self.__predictions = None
        self.__parser = parser_instance
        self.__model = model_instance
        self.__tester = tester.Tester()

        if parser_instance is not None and model_instance is not None:
            return

        self.__read_config(config_filename)

    def __read_config(self, config_filename):
        with open(config_filename, "r") as f:
            self.__parsed_json = json.loads(f.read())

        model_name = self.__parsed_json["model_name"]
        if model_name == "LinearModel":
            self.__model = lm.LinearModel()
            self.__parser = lmp.LinearModelParser()
        elif model_name == "RidgeCV":
            self.__model = lm.RidgeCVModel()
            self.__parser = lmp.LinearModelParser()
        elif model_name == "KNearestNeighbors":
            self.__model = knn.KNearestNeighborsModel()
            self.__parser = lmp.LinearModelParser()
        elif model_name == "RandomForest":
            self.__model = rf.ExtraTreesModel()
            self.__parser = lmp.LinearModelParser()
        else:
            raise ValueError("No metric with given name!")

    def __input(self, filepath_or_buffer, **kwargs):
        """
        An additional method that loads data and divides it into test and
        validation samples.

        :param filepath_or_buffer: same as Parser.parse or self.predict

        :param kwargs: dict
            Passes additional arguments to the parser.parse method.
        """
        self.__parser.parse(filepath_or_buffer, to_list=True, **kwargs)

    def output(self, output_filename="result"):
        """
        Output current prediction to filename.

        :param output_filename: str
            Filename to output.
        """
        predictions = [x.tolist() for x in self.__predictions]
        int_prediction = [[int(round(x)) for x in lst] for lst in predictions]
        predictions = [lmp.LinearModelParser.to_final_label2(x)
                       for x in int_prediction]

        out = pd.DataFrame(predictions, dtype=np.int64)
        out.to_csv(f"{output_filename}.csv", index=False, header=False)

    def predict(self, filepath_or_buffer, **kwargs):
        """
        Make prediction for input dataset.

        :param filepath_or_buffer: str, pathlib.Path, py._path.local.LocalPath
            or any object with a read() method (such as a file handle or
            StringIO)
            The string could be a URL. Valid URL schemes include http, ftp, s3,
            and file. For file URLs, a host is expected. For instance, a local
            file could be file://localhost/path/to/table.csv.

        :param kwargs: dict
            Passes additional arguments to the parser.parse method.
        """
        self.__input(filepath_or_buffer, **kwargs)
        self.__model.train(*self.__parser.get_train_data())

        validation_samples, self.__validation_labels = \
            self.__parser.get_validation_data()

        self.__predictions = self.__model.predict(validation_samples,
                                                  self.__validation_labels)

    def test(self):
        """
        Test prediction quality of algorithm.
        """
        test_result = self.__tester.test(self.__validation_labels,
                                         self.__predictions)

        quality = self.__tester.quality_control(self.__validation_labels,
                                                self.__predictions)

        print(f"Metrics: {test_result}")
        print(f"Quality satisfaction: {quality}")

    def save_model(self, filename="model"):
        """
        Save trained model with all parameters to file.

        :param filename: str
            Filename of model.
        """
        with open(f"models/{filename}.mdl", "wb") as output_stream:
            output_stream.write(pickle.dumps(self.__model.model))


def test_linear():
    sh = Shell()
    sh.predict("data/tinkoff/train.csv")
    sh.test()
    sh.output()


def main():
    logger.setup_logging()
    test_linear()

    # Example of execution:
    # sh = Shell()
    # sh.predict()
    # sh.test()
    # sh.save_model()
    # sh.output()


if __name__ == "__main__":
    main()
