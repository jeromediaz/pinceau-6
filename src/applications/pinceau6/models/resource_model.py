import logging
from string import Template
from typing import Type, TYPE_CHECKING, Mapping, Any, cast

from core.models.a_model import AModel
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from core.managers.model_manager import ModelsManager

logger = logging.getLogger(__name__)


class ResourceModel(AModel):
    META_MODEL = "resource_model"

    layout: str = "simple"
    model_name: str
    parent_model: str
    is_abstract: bool = False
    taxonomies: list[str] = ["/"]
    fields: list[Mapping[str, Any]] = []

    label_format: str = "$id"

    def as_dict(self, **kwargs) -> Mapping[str, Any]:

        return {
            **self.model_dump(mode="json", by_alias=True),
        }

    @classmethod
    def ui_model_layout(cls) -> str:
        return "tabbed"

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:

        return [
            {
                "type": "tab",
                "opts": ["grid"],
                "label": "model",
                "fields": [
                    {
                        "source": "model_name",
                        "type": "text",
                        "label": "Model Name",
                        "grid": {"xs": 12, "sm": 3},
                    },
                    {
                        "source": "is_abstract",
                        "type": "bool",
                        "label": "Abstract model?",
                        "grid": {"xs": 12, "sm": 3},
                    },
                    {
                        "source": "parent_model",
                        "type": "text",
                        "label": "Parent model Name",
                        "defaultValue": "amodel",
                        "grid": {"xs": 12, "sm": 3},
                    },
                    {
                        "source": "label_format",
                        "type": "text",
                    },
                    {
                        "source": "layout",
                        "type": "select",
                        "choices": [
                            {"id": "simple", "name": "Simple"},
                            {"id": "tabbed", "name": "Tabbed"},
                            {"id": "grid", "name": "Grid"},
                        ],
                        "grid": {"xs": 12, "sm": 3},
                    },
                    {
                        "source": "categories",
                        "type": "text",
                        "opts": ["fullWidth"],
                        "multiple": True,
                        "defaultValue": "/",
                    },
                ],
            },
            {
                "type": "tab",
                "label": "fields",
                "fields": [
                    {
                        "source": "fields",
                        "type": "group",
                        "multiple": True,
                        "hideOn": ["list"],
                        "opts": ["grid"],
                        "fields": [
                            {
                                "source": "type",
                                "type": "select",
                                "choices": [
                                    {"id": "text", "name": "Text"},
                                    {"id": "url", "name": "Url"},
                                    {"id": "email", "name": "Email"},
                                    {"id": "bool", "name": "Boolean"},
                                    {"id": "int", "name": "Integer"},
                                    {"id": "float", "name": "Float"},
                                    {"id": "reference", "name": "Reference"},
                                    {"id": "time", "name": "Time"},
                                    {"id": "datetime", "name": "Datetime"},
                                    {"id": "date", "name": "Date"},
                                    {"id": "group", "name": "Group"},
                                    {"id": "select", "name": "Select"},
                                    {"id": "spacer", "name": "Spacer"},
                                ],
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "source",
                                "type": "text",
                                "grid": {"xs": 12, "sm": 6},
                                "condition": {"type": {"$nin": ["spacer", None]}},
                            },
                            {
                                "source": "opts",
                                "type": "select",
                                "multiple": True,
                                "choices": [
                                    {"id": "fullWidth", "name": "Full Width"},
                                    {"id": "multiline", "name": "Multi Line"},
                                    {"id": "inline", "name": "Inline"},
                                    {"id": "grid", "name": "Grid layout"},
                                ],
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "optional",
                                "type": "bool",
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "multiple",
                                "type": "bool",
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "defaultValue",
                                "type": "text",
                                "optional": True,
                                "condition": {"type": "select"},
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "reference",
                                "type": "text",
                                "condition": {"type": "reference"},
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "choices",
                                "type": "group",
                                "multiple": True,
                                "fields": [
                                    {"source": "id", "type": "text"},
                                    {"source": "name", "type": "text"},
                                ],
                                "condition": {"type": "select"},
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "hideOn",
                                "type": "select",
                                "optional": True,
                                "multiple": True,
                                "choices": [{"id": "list", "name": "List"}],
                                "grid": {"xs": 12, "sm": 6},
                            },
                            {
                                "source": "render",
                                "type": "select",
                                "optional": True,
                                "choices": [{"id": "chip", "name": "chip"}],
                                "condition": {"type": "text"},
                                "defaultValue": "chip",
                                "grid": {"xs": 12, "sm": 6},
                            },
                        ],
                    }
                ],
            },
        ]

    def as_class(self, models_manager: "ModelsManager") -> Type[AModel]:
        class_name = self.model_name.title()
        parent_model_definition = models_manager.get_model(self.parent_model)
        if not parent_model_definition:
            raise ValueError("No model named {} found".format(self.parent_model))
        parent_model_class = parent_model_definition.cls

        def model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT):
            parent_model_fields = parent_model_class.ui_model_fields(
                display_mode=display_mode
            )

            return [*parent_model_fields, *self.fields]

        def model_layout(cls):
            return self.layout

        label_format = self.label_format

        def template_label(instance) -> str:
            template = Template(label_format)

            return template.substitute(instance.model_dump(mode="json"))

        model_class = type(
            class_name,
            (parent_model_class,),
            {
                "IS_ABSTRACT": self.is_abstract,
                "ui_model_fields": classmethod(model_fields),
                "ui_model_layout": classmethod(model_layout),
                "label": property(template_label),
                "META_MODEL": self.model_name,
            },
        )

        return cast(Type[AModel], model_class)

    def after_save_handler(self, context):
        super().after_save_handler(context)
        from core.context.global_context import GlobalContext

        global_context = context.cast_as(GlobalContext)
        models_manager = global_context.models_manager
        models_manager.register_model(self.model_name, self.as_class(models_manager))

        logger.info("Registering %s model", self.model_name)

    def after_delete_handler(self, context):
        from core.context.global_context import GlobalContext

        global_context = context.cast_as(GlobalContext)
        models_manager = global_context.models_manager
        models_manager.unregister_model(self.model_name)

        logger.info("Unregistering %s model", self.model_name)

        super().after_delete_handler(context)
