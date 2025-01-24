from typing import ClassVar, Mapping, Any

from bson import SON

from core.context.global_context import GlobalContext
from core.models.a_model import AModel
from core.models.types import ModelUsageMode
from misc.mongodb_helper import mongodb_collection
from ui.ag_charts_field import AGChartsField, AGChartsObject


class MongoFacet(AModel):
    META_MODEL = "mongo_facet"

    IS_ABSTRACT: ClassVar[bool] = True

    dbms_link: str = "mongodb"
    database: str
    collection: str
    field_name: str

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "dbms_link": self.dbms_link,
            "database": self.database,
            "collection": self.collection,
            "field_name": self.field_name,
            "facets": self._facet_values(),
        }

    def _facet_values(self):
        context = GlobalContext.get_instance()
        mongo_collection = mongodb_collection(
            context, self.dbms_link, self.database, self.collection
        )

        results = mongo_collection.aggregate(
            [
                {
                    "$group": {
                        "_id": f"${self.field_name}",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": SON([("count", -1), ("_id", -1)])},
            ]
        )

        return [[result["_id"], result["count"]] for result in results]

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        loss_chart = AGChartsField(source="facets")
        loss_chart.title["text"] = "Category"

        loss_chart.series.append(
            AGChartsObject(type="pie", angleKey="1", legendItemKey="0")
        )

        return [
            {
                "source": "dbms_link",
                "type": "text",
            },
            {"source": "database", "type": "text"},
            {"source": "collection", "type": "text"},
            {"source": "field_name", "type": "text"},
            {
                "source": "facet",
                "hideOn": ["list"],
                **loss_chart.as_ui_field(for_task=None),
            },
        ]
