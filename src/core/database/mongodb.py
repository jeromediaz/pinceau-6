import logging
from typing import (
    Any,
    Iterable,
    Optional,
    Union,
    Mapping,
    TYPE_CHECKING,
    List,
    Tuple,
    TypeVar,
    Type,
)

import pymongo
from bson import ObjectId
from pydantic import BaseModel

from api.helpers import get_sort
from core.models.a_model import AModel
from core.models.types import ModelUsageMode
from misc.mongodb_helper import mongodb_database

if TYPE_CHECKING:
    from core.context.context import Context

logger = logging.getLogger(__name__)

ModelClass = TypeVar("ModelClass", bound="AModel")


class MongoDBHandler:
    def __init__(self, database):
        self._database = database

    @classmethod
    def from_default(
        cls, context: "Context", *, db_link="mongodb", database="pinceau6"
    ):
        database = mongodb_database(context, db_link, database)

        return cls(database)

    @classmethod
    def get_model_class(cls, model: str):
        from core.context.global_context import GlobalContext

        global_context = GlobalContext.get_instance()

        model_def = global_context.models_manager.get_model(model)
        if not model_def:
            return None
        return model_def.cls

    @classmethod
    def load_object(cls, row: dict) -> "AModel":
        work_row = row.copy()

        model: str
        if "_meta" in work_row and "model" in work_row["_meta"]:
            model = work_row["_meta"]["model"]
        else:
            model: str = (
                work_row.pop("_model")
                if "_model" in work_row
                else work_row.pop("model")
            )

        my_class = cls.get_model_class(model)

        if not my_class:
            print("Unable to find model_class for model " + model)
            logger.error("Unable to find model_class for model %s", model)

        my_instance = my_class(**work_row)

        return my_instance

    @staticmethod
    def mongo_payload(
        model: Union[AModel, Mapping[str, Any], BaseModel]
    ) -> Mapping[str, Any]:
        if isinstance(model, AModel):
            data = dict(model.as_dict(mode="python"))

            data["_id"] = data.pop("id", None)

            return data

        elif isinstance(model, Mapping):
            return model

        elif isinstance(model, BaseModel):
            return model.model_dump(mode="json", by_alias=True)

        raise ValueError(
            f"Unsupported model type {type(model)} expected dict or AModel instance"
        )

    def insert_objects(
        self, context: "Context", data_list: List[AModel], collection: str
    ):

        for data in data_list:
            data.before_save_handler(context)

        mongo_data_list = [
            dict(MongoDBHandler.mongo_payload(data)) for data in data_list
        ]

        db_collection = self._database[collection]
        results = db_collection.insert_many(mongo_data_list)

        for data, result_id in zip(data_list, results.inserted_ids):
            data.set_oid(result_id)

            data.after_save_handler(context)

    def save_object(
        self,
        context: "Context",
        data: AModel,
        collection: Optional[str] = None,
        skip_hooks: bool = False,
    ):
        if not skip_hooks:
            data.before_save_handler(context)

        mongo_data = dict(MongoDBHandler.mongo_payload(data))

        if not collection:
            collection = mongo_data.get("_model")

        db_collection = self._database[collection]
        object_id = mongo_data.pop("_id", None)
        if object_id:
            db_collection.update_one(
                {"_id": ObjectId(object_id)}, {"$set": mongo_data}, upsert=True
            )
        else:
            result = db_collection.insert_one(mongo_data)

            if isinstance(data, AModel):
                data.set_oid(result.inserted_id)

        if not skip_hooks:
            data.after_save_handler(context)

    def delete_model_objects(
        self, context: "Context", model_objects: List[AModel], collection: str
    ):
        db_collection = self._database[collection]

        for model_object in model_objects:
            model_object.before_delete_handler(context)

        db_collection.delete_many(
            {
                "_id": {
                    "$in": [ObjectId(model_object.id) for model_object in model_objects]
                }
            }
        )

        for model_object in model_objects:
            model_object.after_delete_handler(context)

    def delete_model_object(
        self, context: "Context", model_object: AModel, collection: str
    ):
        db_collection = self._database[collection]

        model_object.before_delete_handler(context)

        db_collection.delete_one({"_id": ObjectId(model_object.id)})

        model_object.after_delete_handler(context)

    def delete_object(self, context: "Context", object_id: str, collection: str):

        db_collection = self._database[collection]

        value = db_collection.find_one({"_id": ObjectId(object_id)})

        model_object = MongoDBHandler.load_object(value)

        self.delete_model_object(context, model_object, collection)

    def update_object(
        self,
        context: "Context",
        model: AModel,
        collection: Optional[str] = None,
        skip_hooks: bool = False,
    ):
        if not skip_hooks:
            model.before_save_handler(context)

        data = dict(MongoDBHandler.mongo_payload(model))

        if not collection:
            collection = data.get("_meta", {}).get("model")

        db_collection = self._database[collection]
        object_id = data.pop("id") if "id" in data else data.pop("_id")

        db_collection.update_one(
            {"_id": ObjectId(object_id)}, {"$set": data}, upsert=True
        )

        if not skip_hooks:
            model.after_save_handler(context)

    def get_instance(
        self, cls: Type[ModelClass], collection: str, object_id: str
    ) -> Optional[ModelClass]:
        single_object = self.load_one(collection, {"_id": ObjectId(object_id)})

        if not single_object:
            return None

        if not isinstance(single_object, cls):
            raise ValueError(
                f"Object {object_id} from {collection} is not of type {cls.__name__} ({single_object.__class__.__name__})"
            )

        return single_object

    def load_one(self, collection: str, query: dict) -> Any:
        db_collection = self._database[collection]

        if "_id" in query and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])

        data = db_collection.find_one(query)

        return self.__class__.load_object(data) if data else None

    def load_multiples(self, collection: str, query: dict) -> Iterable[Any]:
        db_collection = self._database[collection]

        if "_id" in query and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])

        cursor = db_collection.find(query)

        for row in cursor:
            yield self.__class__.load_object(row)

    def search(
        self,
        collection: str,
        /,
        *,
        start: int = 0,
        end: int = 25,
        filters: Optional[Mapping[str, str]] = None,
    ) -> Tuple[Tuple[int, int, int], Iterable[Any]]:
        filters = dict(filters or {})

        db_collection = self._database[collection]
        filter_arg_object = filters if filters else {}

        filter_dict = {}

        search_dict = None

        q_filter = filter_arg_object.pop("q", None)

        if q_filter:
            db_collection.create_index(
                [("_meta.label", pymongo.TEXT)],
                name="text",
                unique=False,
                sparse=True,
            )
            search_dict = {"$match": {"$text": {"$search": q_filter}}}

        and_list: list[Mapping[str, Any]] = list()

        id_filter = filter_arg_object.pop("id", None)
        if id_filter:
            if isinstance(id_filter, list):
                if isinstance(id_filter[0], str):
                    and_list.append(
                        {"_id": {"$in": [ObjectId(val) for val in id_filter]}}
                    )
                else:
                    and_list.append(
                        {"_id": {"$in": [ObjectId(val) for val in id_filter[0]]}}
                    )

            else:
                and_list.append({"_id": ObjectId(id_filter)})

        for key, filter_value in filter_arg_object.items():
            is_reversed = key.startswith("-")
            final_key = key[1:] if is_reversed else key

            if isinstance(filter_value, list):
                instruction = "$nin" if is_reversed else "$in"
                and_list.append({final_key: {instruction: filter_value}})
            else:
                instruction = "$neq" if is_reversed else "$eq"
                and_list.append({final_key: {instruction: filter_value}})

        page_size = end - start + 1
        page = 1 + start / page_size

        aggregate_pipeline: list[Mapping[str, Any]] = []
        if search_dict:
            aggregate_pipeline.append(search_dict)

        if and_list:
            filter_dict["$and"] = and_list

        if filter_dict and filter_dict.get("$and"):
            aggregate_pipeline.append({"$match": filter_dict})

        sort_key, sort_order = get_sort()
        if sort_key and sort_order is not None:
            aggregate_pipeline.append({"$sort": {sort_key: 1 if sort_order else -1}})

        aggregate_pipeline.append(
            {
                "$facet": {
                    "metadata": [{"$count": "totalCount"}],
                    "data": [
                        {"$skip": (page - 1) * page_size},
                        {"$limit": page_size},
                    ],
                },
            },
        )

        values = db_collection.aggregate(aggregate_pipeline)

        value = next(values)

        db_data = value["data"]

        total_count = value["metadata"][0]["totalCount"] if db_data else 0

        items = [
            MongoDBHandler.load_object(item).to_json_dict(
                display_mode=ModelUsageMode.LIST
            )
            for item in db_data
        ]

        end = start + len(items) - 1

        return (start, end, total_count), items
