import inspect
import time
from abc import ABCMeta, ABC
from types import NoneType
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Optional,
    Mapping,
    Any,
    cast,
    Union,
    get_args,
    get_origin,
    Type,
    TypeVar,
    Set,
    Dict,
)

from pydantic import BaseModel, Field, field_validator
from pydantic._internal._model_construction import ModelMetaclass
from pydantic_core.core_schema import ValidationInfo
from pydantic_mongo import ObjectIdField

from core.models.extended_base_model import ExtendedBaseModel
from core.models.types import ModelUsageMode
from ui.helper import ui_fields_from_base_model

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.types import JSONParam


class ModelMeta(ModelMetaclass, ABCMeta):
    def __new__(mcs, name, bases, dct):
        x = super().__new__(mcs, name, bases, dct)

        if "IS_ABSTRACT" not in dct:
            x.IS_ABSTRACT = False

        return x


T = TypeVar("T", bound="AModel")


class MetaObjectModel(BaseModel):
    model: str = ""
    label: Optional[str] = None
    created_by_user: Optional[str] = None
    created_at: Optional[int] = None
    modified_by_user: Optional[str] = None
    modified_at: Optional[int] = None


class AModel(ExtendedBaseModel, ABC, metaclass=ModelMeta):
    META_MODEL: ClassVar[str] = "amodel"
    HIDDEN_FIELDS: ClassVar[Set[str]] = {"id", "meta", "layout", "model"}
    META_LAYOUT: ClassVar[str] = "simple"

    IS_ABSTRACT: ClassVar[bool] = True

    id: Optional[ObjectIdField | str] = Field(
        default=None, alias="_id", serialization_alias="id"
    )
    # model: str = Field(alias="_model", serialization_alias="_model")
    meta: MetaObjectModel = Field(
        MetaObjectModel(), alias="_meta", serialization_alias="_meta"
    )

    class Config:
        extra = "allow"

    def __init__(self, *args, **kwargs) -> None:
        if "_model" not in kwargs:
            kwargs["_model"] = self.__class__.META_MODEL

        if "id" in kwargs:
            kwargs.pop("id")

        if "_model" in kwargs:
            kwargs.setdefault("_meta", {})["model"] = kwargs["_model"]

        super().__init__(*args, **kwargs)

    @classmethod
    def __is_annotation_amodel(cls, annotation: type) -> Optional[Type["AModel"]]:
        if get_origin(annotation) is not Union:
            if not inspect.isclass(annotation):
                return None
            return annotation if issubclass(annotation, AModel) else None

        annotation_args = get_args(annotation)
        if len(annotation_args) != 2:
            return None

        return (
            annotation_args[1]
            if (
                annotation_args[1] is NoneType
                and issubclass(annotation_args[0], AModel)
            )
            else None
        )

    @property
    def others(self) -> Mapping[str, Any]:
        return self.model_extra if self.model_extra else {}

    @field_validator("*", mode="before")
    @classmethod
    def transform(cls, raw: Any, info: ValidationInfo) -> Any:
        if (
            not isinstance(raw, dict)
            or ("_model" not in raw and "_meta" not in raw)
            or (
                not isinstance(raw.get("_model"), str)
                and not isinstance(raw.get("_meta", {}).get("model"), str)
            )
            or not info
            or not info.field_name
        ):
            # legacy
            return raw

        """
        if (
            not isinstance(raw, dict)
            or "meta" not in raw
            or not isinstance(raw.get("meta", {}).get("model"), str)
            or not info
            or not info.field_name
        ):
            return raw
        """

        field = cls.model_fields[info.field_name]
        annotation = field.annotation
        if not annotation:
            return raw

        # TODO: move elsewhere
        check = cls.__is_annotation_amodel(annotation)

        if check:
            # TODO: handle mode handlers
            from core.database.mongodb import MongoDBHandler

            return MongoDBHandler.load_object(raw)

        return raw

    def before_save_handler(self, context: "Context") -> None:
        from core.context.user_context import UserContext

        try:
            user_context = context.cast_as(UserContext)
        except ValueError:
            user_context = None

        if not user_context:
            return

        user_id = user_context.user_id
        now_ts = int(time.time() * 1000)
        if not self.id:
            self.meta.created_by_user = user_id
            self.meta.created_at = now_ts

        self.meta.modified_by_user = user_id
        self.meta.modified_at = now_ts

        print(f"user_id {user_id}")

    def after_save_handler(self, context: "Context") -> None:
        # default implementation does nothing
        pass

    def before_delete_handler(self, context: "Context") -> None:
        # default implementation does nothing
        pass

    def after_delete_handler(self, context: "Context") -> None:
        # default implementation does nothing
        pass

    def set_oid(self, oid_value) -> None:
        if oid_value:
            self.id = oid_value

    def __getattr__(self, item) -> Any:
        return self.model_extra.get(item) if self.model_extra else None

    @property
    def oid(self) -> str:
        return str(self.id)

    def as_dict(
        self, *, mode: str = "json", exclude: Optional[Set[str]] = None
    ) -> Mapping[str, Any]:
        extra_dict = self.model_extra if self.model_extra is not None else {}

        if type(self).as_dict == AModel.as_dict:
            final_exclude = None if not exclude else exclude - {"meta", "model"}

            dict_values = self.model_dump(
                mode=mode, exclude=final_exclude, by_alias=True
            )
        else:
            dict_values = {}

        if isinstance(self.meta, MetaObjectModel):
            self.meta.label = self.meta_label

        data = {
            **extra_dict,
            "_meta": self.meta.model_dump(
                mode="json", exclude_none=True, exclude_unset=True
            ),
            **dict_values,
        }

        if self.id:
            data["id"] = str(self.id)

        return data

    def to_json_dict(self, *, display_mode=ModelUsageMode.DEFAULT) -> "JSONParam":
        hidden_fields = self.hidden_fields(display_mode=display_mode)
        json_dict = self.as_dict(exclude=hidden_fields)

        import pydash

        json_param = cast("JSONParam", pydash.omit(json_dict, *hidden_fields))

        if self.id:
            json_param["id"] = str(self.id)

        return json_param

    @property
    def meta_label(self) -> str:
        return f"{self.model}#{self.id}"

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return ui_fields_from_base_model(cls, display_mode=display_mode)

    @classmethod
    def ui_model_layout(cls) -> str:
        return cls.META_LAYOUT

    @classmethod
    def downcast(cls: Type[T], instance: "AModel", **kwargs) -> T:
        if not issubclass(cls, type(instance)):
            raise RuntimeError(
                f"Cannot downcast from {type(instance).__name__} to {cls.__name__}"
            )
        if isinstance(instance, cls):
            return cast(T, instance)

        new_object_args = {**instance.as_dict(), **kwargs}

        meta = new_object_args.setdefault("_meta", {})
        meta["model"] = cls.META_MODEL

        new_object = cls(**new_object_args)
        new_object.set_oid(instance.oid)

        return cast(T, new_object)

    def dump_as_json(self, *, exclude: Optional[Set[str]] = None) -> Mapping[str, Any]:
        dump_dict: Dict[str, Any] = self.model_dump(
            mode="json", by_alias=True, exclude=exclude, exclude_unset=True
        )

        if not self.id:
            dump_dict.pop("id", None)

        meta_object = dump_dict.setdefault("_meta", {})
        meta_object["label"] = self.meta_label

        if "model" not in meta_object and "_model" in dump_dict:
            meta_object["model"] = dump_dict.pop("_model")

        return dump_dict

    def dump_as_map(self) -> Mapping[str, Any]:
        dump_dict: Dict[str, Any] = self.model_dump(mode="python", by_alias=True)

        if not self.id:
            del dump_dict["id"]

        dump_dict.setdefault("_meta", {})["label"] = self.meta_label

        return dump_dict

    def load_reference(self, context: "Context", field: str, model_class: Type[T]) -> T:
        from core.database.mongodb import MongoDBHandler

        model_field = self.model_fields.get(field)
        if not model_field:
            raise ValueError(f"Unknown field: {field} in {self.__class__.__name__}")

        json_schema_extra = model_field.json_schema_extra

        if not isinstance(json_schema_extra, dict):
            raise ValueError("Un-valid json_schema_extra")

        field_type = json_schema_extra.get("type")
        reference = json_schema_extra.get("reference")

        if not isinstance(field_type, str) or field_type != "reference":
            raise ValueError(
                f"Field {field} is not a reference for {self.__class__.__name__}"
            )

        if not isinstance(reference, str) or not reference:
            raise ValueError(
                f"Field {field} is missing a reference for {self.__class__.__name__}"
            )

        _, provider, collection = reference.split("/")
        if provider != "mongodb":
            raise ValueError(f"Provider {provider} is not supporter")

        object_id = getattr(self, field)

        return MongoDBHandler.from_default(context).get_instance(
            model_class, collection, object_id
        )
