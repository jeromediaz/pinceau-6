from typing import (
    Any,
    Iterable,
    Optional,
    Union,
    Mapping,
    TYPE_CHECKING,
    List,
    Tuple,
)

from core.models.a_model import AModel
from misc.elastic_helper import elasticsearch_client

if TYPE_CHECKING:
    from core.context.context import Context


class EsIndexHandler:
    def __init__(self, elastic, index):
        self._elastic = elastic
        self._index = index

    @classmethod
    def from_default(
        cls, context: "Context", *, db_link="elasticsearch", index="pinceau6"
    ):
        elastic = elasticsearch_client(context, db_link)

        return cls(elastic, index)

    @classmethod
    def get_model_class(cls, model: str):
        from core.context.global_context import GlobalContext

        global_context = GlobalContext.get_instance()

        model_def = global_context.models_manager.get_model(model)
        if not model_def:
            return None
        return model_def.cls

    @classmethod
    def load_object(cls, row: dict, as_model=None) -> Any:
        work_row = row.copy()

        model: str = (
            as_model
            if as_model
            else (
                work_row.pop("_model")
                if "_model" in work_row
                else work_row.pop("model")
            )
        )

        my_class = cls.get_model_class(model)

        work_row.pop("embedding", "")

        my_instance = my_class(**work_row)

        return my_instance

    @staticmethod
    def es_payload(model: Union[AModel, Mapping[str, Any]]) -> Mapping[str, Any]:
        if isinstance(model, AModel):
            data = dict(model.as_dict())

            data["_id"] = data.pop("id", None)

            return data

        elif isinstance(model, Mapping):
            return model

        raise ValueError(
            f"Unsupported model type {type(model)} expected dict or AModel instance"
        )

    def insert_objects(self, context: "Context", data_list: List[AModel], index: str):
        del index  # not used for elasticsearch

        for model_object in data_list:
            model_object.before_save_handler(context)

        # TODO: use bulk !!!!!
        for model_object in data_list:
            result = self._elastic.index(
                index=self._index, body=dict(EsIndexHandler.es_payload(model_object))
            )
            # TODO:

            model_object.after_save_handler(context)

    def save_object(
        self, context: "Context", data: AModel, index: Optional[str] = None
    ):
        # ICI: handler before save

        data.before_save_handler(context)

        es_data = dict(EsIndexHandler.es_payload(data))

        if not index:
            index = es_data.get("_model")

        object_id = es_data.pop("_id", None)
        if object_id:
            self._elastic.index(index=self._index, id=object_id, body=es_data)

        else:
            result = self._elastic.index(index=self._index, body=es_data)

        data.after_save_handler(context)

    def delete_object(self, context: "Context", object_id: str, collection: str):
        del collection  # not used for elasticsearch

        value = self._elastic.get(index=self._index, id=object_id)

        model_object = EsIndexHandler.load_object(value)

        model_object.before_delete_handler(context)

        self._elastic.delete(index=self._index, id=object_id)

        model_object.after_delete_handler(context)

    def update_object(
        self,
        context: "Context",
        model: AModel,
        collection: Optional[str] = None,
    ):
        model.before_save_handler(context)

        data = dict(EsIndexHandler.es_payload(model))

        if not collection:
            collection = data.get("_model")

        object_id = data.pop("id") if "id" in data else data.pop("_id")

        self._elastic.index(index=self._index, id=object_id, body=data)

        model.after_save_handler(context)

    def load_one(self, query: dict, as_model=None) -> Any:

        data = None
        if "_id" in query and isinstance(query["_id"], str):
            data = self._elastic.get(index=self._index, id=query["_id"])

        return self.__class__.load_object(data, as_model=as_model) if data else None

    def load_multiples(self, collection: str, query: dict) -> Iterable[Any]:
        raise NotImplementedError

    def search(
        self,
        collection: str,
        /,
        *,
        start: int = 0,
        end: int = 25,
        filters: Optional[Mapping[str, str]] = None,
    ) -> Tuple[Tuple[int, int, int], Iterable[Any]]:
        del collection  # not used for elasticsearch

        filters = dict(filters or {})

        filter_arg_object = filters if filters else {}

        q_filter = filter_arg_object.pop("q", None)

        res = self._elastic.search(
            index=self._index, q=q_filter, from_=start, size=end - start
        )

        payload = res.body
        total_count = payload.get("hits", {}).get("total", 0)
        db_data = payload["hits"]["hits"]
        items = [
            EsIndexHandler.load_object(
                {"_id": item["_id"], **item["_source"]}, as_model="amodel"
            ).to_json_dict()
            for item in db_data
        ]

        end = start + len(items) - 1

        return (start, end, total_count), items
