import logger
import pickle
import tester

import numpy as np
import pandas as pd

import parsers.parser as ipar
import parsers.linear_model_parser as lmp
import parsers.config_parsers as cnfp

import models.model as mdl


@logger.decor_class_logging_error_and_time()
class Shell:

    def __init__(self, config_filename="ml_config.json"):
        """
        Constructor which initialize class fields.

        :param config_filename: str, optional (default="ml_config.json")
            Name of the json file with configuration.
        """
        self._validation_labels = None
        self._predictions = None
        self._config_parser = cnfp.ConfigParser(config_filename)
        self._model_parameters = dict()
        self._tester = tester.Tester()

        model_name = self._config_parser["model_name"]
        model_module_name = self._config_parser["model_module_name"]
        parser_name = self._config_parser["parser_name"]
        parser_module_name = self._config_parser["parser_module_name"]
        self._model_parameters = self._config_parser["model_parameters"]

        self._model = self._config_parser.get_instance(
            model_name, model_module_name
        )
        self._parser = self._config_parser.get_instance(
            parser_name, parser_module_name, debug=self.is_debug()
        )

        # assert self._check_interfaces()

    def _input(self, filepath_or_buffer, **kwargs):
        """
        An additional method that loads data and divides it into test and
        validation samples.

        :param filepath_or_buffer: same as Parser.parse or self.predict

        :param kwargs: dict
            Passes addition79al arguments to the parser.parse method.
        """
        self._parser.parse(filepath_or_buffer, to_list=True, **kwargs)

    @staticmethod
    def _check_interface(instance, parent_class):
        """
        Checks the classes on the according interfaces.

        :param instance: object
            Object to check.

        :param parent_class: class
            Class to verify.

        :return: bool
            Results of verifying.
        """
        return issubclass(instance, parent_class)

    def _check_interfaces(self):
        """
        Checks parser and model classes on the according interfaces.

        :return: bool
            Status of verifying.
        """
        return self._check_interface(self._parser, ipar.IParser) and \
            self._check_interface(self._model, mdl.IModel)

    def is_debug(self, flag_name="debug"):
        """
        Return debug status of the program.

        :param flag_name: str, optional (default="debug")
            Name of the debug flag in config.

        :return: bool
            Value of debug flag.
        """
        return self._config_parser[flag_name]

    @property
    def predictions(self):
        """
        Get current results of prediction.

        :return: list
            Current predictions.
        """
        return self._predictions

    def get_formatted_predictions(self):
        """
        Format raw results of prediction.

        :return: list
            Formatted predictions.
        """
        predictions = [x.tolist() for x in self._predictions]
        int_prediction = [[int(round(x)) for x in lst] for lst in predictions]
        predictions = [lmp.LinearModelParser.to_final_label(x)
                       for x in int_prediction]
        return predictions

    def output(self, output_filename="result"):
        """
        Output current prediction to filename.

        :param output_filename: str, optional (default="result")
            Filename to output.
        """
        predictions = self.get_formatted_predictions()

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
        self._input(filepath_or_buffer, **kwargs)
        self._model.train(*self._parser.get_train_data())

        validation_samples, self._validation_labels = \
            self._parser.get_validation_data()

        self._predictions = self._model.predict(validation_samples,
                                                self._validation_labels)

    def test(self):
        """
        Test prediction quality of algorithm.
        """
        test_result = self._tester.test(self._validation_labels,
                                        self._predictions)

        quality = self._tester.quality_control(self._validation_labels,
                                               self._predictions)

        print(f"Metrics: {test_result}")
        print(f"Quality satisfaction: {quality}")

    def save_model(self, filename="model"):
        """
        Save trained model with all parameters to file.

        :param filename: str, optional (default="model")
            Filename of model.
        """
        with open(f"models/{filename}.mdl", "wb") as output_stream:
            output_stream.write(pickle.dumps(self._model.model))


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
