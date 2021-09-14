import inspect
from typing import Union, Optional

import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from gama.search_methods.pygmo_search import SearchPygmo

from .gama import Gama
from gama.data_loading import X_y_from_file
from gama.configuration.classification import clf_config
from gama.utilities.metrics import scoring_to_metric


class GamaClassifier(Gama):
    """ Gama with adaptations for (multi-class) classification. """

    def __init__(self, config=None, scoring="neg_log_loss", *args, **kwargs):
        if not config:
            # Do this to avoid the whole dictionary being included in the documentation.
            config = clf_config

        self._metrics = scoring_to_metric(scoring)
        if any(metric.requires_probabilities for metric in self._metrics):
            # we don't want classifiers that do not have `predict_proba`,
            # because then we have to start doing one hot encodings of predictions etc.
            config = {
                alg: hp
                for (alg, hp) in config.items()
                if not (
                    inspect.isclass(alg)
                    and issubclass(alg, ClassifierMixin)
                    and not hasattr(alg(), "predict_proba")
                )
            }

        self._label_encoder = None
        super().__init__(*args, **kwargs, config=config, scoring=scoring)

    def _predict(self, x: pd.DataFrame):
        """ Predict the target for input X.

        Parameters
        ----------
        x: pandas.DataFrame
            A dataframe with the same number of columns as the input to `fit`.

        Returns
        -------
        numpy.ndarray
            Array with predictions of shape (N,) where N is len(X).
        """
        y = self.model.predict(x)  # type: ignore
        # Decode the predicted labels - necessary only if ensemble is not used.
        if y[0] not in self._label_encoder.classes_:
            y = self._label_encoder.inverse_transform(y)
        return y

    def _predict_proba(self, x: pd.DataFrame):
        """ Predict the class probabilities for input x.

        Predict target for x, using the best found pipeline(s) during the `fit` call.

        Parameters
        ----------
        x: pandas.DataFrame
            A dataframe with the same number of columns as the input to `fit`.

        Returns
        -------
        numpy.ndarray
            Array of shape (N, K) with class probabilities where N is len(x),
             and K is the number of class labels found in `y` of `fit`.
        """
        return self.model.predict_proba(x)  # type: ignore

    def predict_proba(self, x: Union[pd.DataFrame, np.ndarray]):
        """ Predict the class probabilities for input x.

        Predict target for x, using the best found pipeline(s) during the `fit` call.

        Parameters
        ----------
        x: pandas.DataFrame or numpy.ndarray
            Data with the same number of columns as the input to `fit`.

        Returns
        -------
        numpy.ndarray
            Array of shape (N, K) with class probabilities where N is len(x),
             and K is the number of class labels found in `y` of `fit`.
        """
        x = self._prepare_for_prediction(x)
        return self._predict_proba(x)

    def predict_proba_from_file(
        self,
        arff_file_path: str,
        target_column: Optional[str] = None,
        encoding: Optional[str] = None,
    ):
        """ Predict the class probabilities for input in the arff_file.

        Parameters
        ----------
        arff_file_path: str
            An ARFF file with the same columns as the one that used in fit.
            Target column must be present in file, but its values are ignored.
        target_column: str, optional (default=None)
            Specifies which column the model should predict.
            If left None, the last column is taken to be the target.
        encoding: str, optional
            Encoding of the ARFF file.

        Returns
        -------
        numpy.ndarray
            Numpy array with class probabilities.
            The array is of shape (N, K) where N is len(X),
            and K is the number of class labels found in `y` of `fit`.
        """
        x, _ = X_y_from_file(arff_file_path, target_column, encoding)
        x = self._prepare_for_prediction(x)
        return self._predict_proba(x)

    def fit(self, x, y, *args, **kwargs):
        """ Should use base class documentation. """
        # X_support = x.copy()
        # y_support = y.copy()
        # Data = {
        # for percentage_split in [0.9, 0.7, 0.5, 0.3, 0.1, 0.05]:
        #     print("Evaluation with", 1-percentage_split, " of the data, GamaClassifier")
        #     print("X_support.shape", X_support.shape)
        #     print("y_support.shape", y_support.shape)
        #     X_train, X_test, y_train, y_test = train_test_split(X_support, y_support, test_size=percentage_split, stratify=y, random_state=0)
        
        # X_support = x.copy()
        # y_support = y.copy()
        # data_storage = {}
        # SuccessiveHalving = [0.9, 0.7, 0.5, 0.3, 0.1, 0.05]
        # for percen in SuccessiveHalving:
        #     X_train, _, y_train, _ = train_test_split(X_support, y_support, test_size=percen, stratify=y, random_state=0)
        #     data_storage["X_train"+str(percen)] = X_train
        #     data_storage["y_train"+str(percen)] = y_train
        # for i in range(len(SuccessiveHalving)):
        #     print("X_train +str(SuccessiveHalving[i])", "X_train"+str(SuccessiveHalving[i]))
        #     print("y_train +str(SuccessiveHalving[i])", "y_train"+str(SuccessiveHalving[i]))
        #     x = data_storage["X_train"+str(SuccessiveHalving[i])]
        #     y = data_storage["y_train"+str(SuccessiveHalving[i])]
        if isinstance(self._search_method, SearchPygmo):
            print("Vamos a evaluar con succesive halving en GamaClassifier")
            X_support = x.copy()
            y_support = y.copy()
            data_storage = {}
            SuccessiveHalving = [0.8, 0.6, 0.4, 0.2, 0.05]
            for percen in SuccessiveHalving:
                X_train, _, y_train, _ = train_test_split(X_support, y_support, test_size=percen, stratify=y, random_state=0)
                data_storage["X_train"+str(percen)] = X_train
                data_storage["y_train"+str(percen)] = y_train
            for i in range(len(SuccessiveHalving)):
                #print("X_train +str(SuccessiveHalving[i])", "X_train"+str(SuccessiveHalving[i]))
                #print("y_train +str(SuccessiveHalving[i])", "y_train"+str(SuccessiveHalving[i]))
                x = data_storage["X_train"+str(SuccessiveHalving[i])]
                y = data_storage["y_train"+str(SuccessiveHalving[i])]
                y_ = y.squeeze() if isinstance(y, pd.DataFrame) else y
                self._label_encoder = LabelEncoder().fit(y_)
                if any([isinstance(yi, str) for yi in y_]):
                    # If target values are `str` we encode them or scikit-learn will complain.
                    y = self._label_encoder.transform(y_)
                # print("Sigo en gama Classifier, porcentaje de datos es", 1-SuccessiveHalving[i])
                self._evaluation_library.determine_sample_indices(stratify=y)
                super().fit(x, y, *args, **kwargs)
        else:
            y_ = y.squeeze() if isinstance(y, pd.DataFrame) else y
            self._label_encoder = LabelEncoder().fit(y_)
            if any([isinstance(yi, str) for yi in y_]):
                # If target values are `str` we encode them or scikit-learn will complain.
                y = self._label_encoder.transform(y_)
            # print("Sigo en gama Classifier, porcentaje de datos es", 1-SuccessiveHalving[i])
            self._evaluation_library.determine_sample_indices(stratify=y)
            super().fit(x, y, *args, **kwargs)
        # print("2 Sigo en gama Classifier, porcentaje de datos es", 1-SuccessiveHalving[i])
            
    def _encode_labels(self, y):
        self._label_encoder = LabelEncoder().fit(y)
        return self._label_encoder.transform(y)
