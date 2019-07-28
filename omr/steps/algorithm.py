from abc import ABC, abstractmethod
from database import DatabaseBook, DatabasePage
from database.file_formats import PcGts
from omr.dataset import DatasetCallback, Dataset
from typing import Optional, List, Type, Union
from .algorithmtrainerparams import AlgorithmTrainerSettings, AlgorithmTrainerParams, DatasetParams
from .algorithmpreditorparams import AlgorithmPredictorSettings, AlgorithmPredictorParams
from database.model import Models, Model, ModelMeta
from database.database_available_models import DatabaseAvailableModels
import os
import uuid
from .algorithmtypes import AlgorithmTypes, AlgorithmGroups


class TrainerCallback(DatasetCallback, ABC):
    def __init__(self):
        super().__init__()
        self.total_iters = 0
        self.early_stopping_iters = 0

    def init(self, total_iters, early_stopping_iters):
        self.total_iters = total_iters
        self.early_stopping_iters = early_stopping_iters

    @abstractmethod
    def next_iteration(self, iter: int, loss: float, acc: float):
        pass

    @abstractmethod
    def next_best_model(self, best_iter: int, best_acc: float, best_iters: int):
        pass

    @abstractmethod
    def early_stopping(self):
        pass

    @abstractmethod
    def resolving_files(self):
        pass


class PredictionCallback(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def progress_updated(self,
                         percentage: float,
                         n_pages: int = 0,
                         n_processed_pages: int = 0):
        pass


class AlgorithmTrainer(ABC):
    @staticmethod
    @abstractmethod
    def meta() -> Type['AlgorithmMeta']:
        pass

    @staticmethod
    @abstractmethod
    def default_params() -> AlgorithmTrainerParams:
        pass

    def __init__(self, settings: AlgorithmTrainerSettings):
        super().__init__()
        self.settings: AlgorithmTrainerSettings = settings
        if not self.settings.params:
            self.settings.params = self.__class__.default_params()

        self.params: AlgorithmTrainerParams = self.settings.params
        self.train_dataset = self.meta().dataset_class()(self.settings.train_data, self.settings.dataset_params)
        self.validation_dataset = self.meta().dataset_class()(self.settings.validation_data, self.settings.dataset_params)

    def train(self, target_book: Optional[DatabaseBook] = None, callback: Optional[TrainerCallback] = None):
        class CallbackInterception(TrainerCallback):
            def __init__(self, model: Model):
                super().__init__()
                self.meta = model.meta()
                self.model = model

            def init(self, total_iters, early_stopping_iters):
                if callback:
                    callback.init(total_iters, early_stopping_iters)

            def next_iteration(self, iter: int, loss: float, acc: float):
                if callback:
                    callback.next_iteration(iter, loss, acc)

            def next_best_model(self, best_iter: int, best_acc: float, best_iters: int):
                if callback:
                    callback.next_best_model(best_iter, best_acc, best_iters)

                self.meta.accuracy = best_acc
                self.meta.iters = best_iter
                self.model.save_meta()

            def early_stopping(self):
                if callback:
                    callback.early_stopping()

            def resolving_files(self):
                if callback:
                    callback.resolving_files()

            def loading(self, n: int, total: int):
                if callback:
                    callback.loading(n, total)

            def loading_started(self, total: int):
                if callback:
                    callback.loading_started(total)

            def loading_finished(self, total: int):
                if callback:
                    callback.loading_finished(total)

        if not self.settings.model:
            if target_book:
                self.settings.model = self.meta().create_new_model(target_book)
            else:
                raise ValueError()
        self.settings.model.save_meta()

        self._pre_train()
        self._train(target_book, CallbackInterception(self.settings.model))
        self._post_train(target_book)

        self.settings.model.save_meta()

    @abstractmethod
    def _train(self, target_book: Optional[DatabaseBook] = None, callback: Optional[TrainerCallback] = None):
        return None

    def _pre_train(self):
        with open(self.settings.model.local_file("dataset_params.json"), 'w') as f:
            f.write(self.settings.dataset_params.to_json(indent=2))

    def _post_train(self, target_book: Optional[DatabaseBook] = None):
        pass


class AlgorithmPredictor(ABC):
    @staticmethod
    @abstractmethod
    def meta() -> Type['AlgorithmMeta']:
        pass

    def __init__(self, settings: AlgorithmPredictorSettings):
        super().__init__()
        self.settings: AlgorithmPredictorSettings = settings
        self.params: AlgorithmPredictorParams = settings.params

        if self.params.modelId:
            # override model if an id is given
            self.settings.model = Model.from_id(self.params.modelId)

        try:
            with open(settings.model.local_file('dataset_params.json'), 'r') as f:
                self.dataset_params = DatasetParams.from_json(f.read())
        except FileNotFoundError:
            self.dataset_params = DatasetParams()

    @abstractmethod
    def predict(self, pages: Union[List[PcGts], List[DatabasePage]], callback: Optional[PredictionCallback] = None):
        pass


class AlgorithmMeta(ABC):
    @staticmethod
    @abstractmethod
    def type() -> AlgorithmTypes:
        pass

    @classmethod
    def group(cls) -> AlgorithmGroups:
        return cls.type().group()

    @classmethod
    @abstractmethod
    def trainer(cls) -> Type[AlgorithmTrainer]:
        pass

    @classmethod
    @abstractmethod
    def predictor(cls) -> Type[AlgorithmPredictor]:
        pass

    @classmethod
    def create_trainer(cls, settings: AlgorithmTrainerSettings) -> AlgorithmTrainer:
        return cls.trainer()(settings)

    @classmethod
    def create_predictor(cls, settings) -> AlgorithmPredictor:
        return cls.predictor()(settings)

    @staticmethod
    @abstractmethod
    def dataset_class() -> Type[Dataset]:
        pass

    @staticmethod
    @abstractmethod
    def model_dir() -> str:
        pass

    @classmethod
    def models_for_book(cls, book: DatabaseBook) -> Models:
        return Models(book.local_models_path(cls.model_dir()))

    @classmethod
    def default_model_for_book(cls, book: DatabaseBook) -> Model:
        return Model(book.local_default_models_path(cls.model_dir()))

    @classmethod
    def default_model_for_style(cls, style: str) -> Optional[Model]:
        from database.database_available_models import DatabaseAvailableModels
        model = Model(DatabaseAvailableModels.local_default_model_path_for_style(style, cls.model_dir()))
        if model.exists():
            return model
        return None

    @classmethod
    def model_path(cls, book: DatabaseBook, s: str):
        return book.local_models_path(os.path.join(cls.model_dir(), s))

    @classmethod
    def newest_model_for_book(cls, book: Optional[DatabaseBook]) -> Optional[Model]:
        if not book:
            return None

        best_model = cls.models_for_book(book).newest_model()
        if best_model and best_model.exists():
            return best_model

        return None

    @classmethod
    def best_model_for_book(cls, book: Optional[DatabaseBook]) -> Optional[Model]:
        newest_model = cls.newest_model_for_book(book)
        if newest_model and newest_model.exists():
            return newest_model

        return cls.default_model_for_book(book)

    @classmethod
    def selected_model_for_book(cls, book: Optional[DatabaseBook]) -> Optional[Model]:
        if not book:
            return None

        selected_model_id = book.get_meta().defaultModels.get(cls.group().value, None)
        if selected_model_id:
            model = Model.from_id(selected_model_id)
            if model and model.exists():
                return model

        best = cls.best_model_for_book(book)
        if best and best.exists():
            return best

        # fallback: french14 must exist
        return cls.default_model_for_style('french14')

    @classmethod
    def model_of_book_style(cls, book: Optional[DatabaseBook]) -> Optional[Model]:
        if not book:
            return None

        model = cls.default_model_for_book(book)
        if model and model.exists():
            return model

        return None

    @classmethod
    def create_new_model(cls, book: DatabaseBook, id: Optional[str] = None) -> Model:
        import datetime

        id = id if id else str(uuid.uuid4())
        time = datetime.datetime.now()
        return Model(cls.model_path(book, time.strftime("%Y-%m-%dT%H:%M:%S")),
                     ModelMeta(id,
                               time)
                     )

    @classmethod
    def list_available_models_for_style(cls, style: str) -> DatabaseAvailableModels:
        default_style_model = cls.default_model_for_style(style).meta() if cls.default_model_for_style(style) else None
        return DatabaseAvailableModels(
            selected_model=default_style_model,
            default_book_style_model=default_style_model,
            models_of_same_book_style=[(b.get_meta(), cls.newest_model_for_book(b).meta()) for b in DatabaseBook.list_available_of_style(style) if cls.newest_model_for_book(b)]
        )

