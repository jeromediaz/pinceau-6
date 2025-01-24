import hashlib
import os
from typing import TYPE_CHECKING, ClassVar, Optional, Set, List, Self, Any

from pydantic import SecretStr, computed_field, model_validator, field_validator
from pydantic_core import ValidationError

from applications.pinceau6.models.character import Character
from applications.pinceau6.models.policy import Policy
from applications.pinceau6.utils import add_user_to_group, remove_user_from_group
from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler
from ui.helper import P6Field, P6ReferenceField

if TYPE_CHECKING:
    from core.context.context import Context


class User(Character):
    META_MODEL: ClassVar[str] = "user"
    HIDDEN_FIELDS: ClassVar[Set[str]] = {"password", "salt"}
    HIDDEN_FIELDS_SHOW: ClassVar[Set[str]] = {
        "old_password",
        "password_input",
        "password_confirm",
    }

    HIDDEN_FIELDS_LIST: ClassVar[Set[str]] = {
        "old_password",
        "password_input",
        "password_confirm",
    }

    HIDDEN_FIELDS_CREATE: ClassVar[Set[str]] = {"old_password"}

    password: Optional[bytes] = None  # Field(None, alias="password")
    salt: Optional[bytes] = None  # Field(None, exclude=False)

    old_password: SecretStr = P6Field(
        SecretStr(""), exclude=True, json_schema_extra={"validations": {"minLength": 0}}
    )
    password_input: SecretStr = P6Field(
        SecretStr(""), exclude=True, json_schema_extra={"validations": {"minLength": 0}}
    )
    password_confirm: SecretStr = P6Field(
        SecretStr(""), exclude=True, json_schema_extra={"validations": {"minLength": 0}}
    )

    groups: List[str] = P6ReferenceField(
        [], reference="data/mongodb/p6_user_group", option_value="principal"
    )

    @field_validator("old_password", mode="before")
    @classmethod
    def transform_pw0(cls, raw: Any) -> SecretStr:
        if raw:
            return SecretStr(raw)
        return SecretStr("")

    @field_validator("password_input", mode="before")
    @classmethod
    def transform_pw1(cls, raw: Any) -> SecretStr:
        if raw:
            return SecretStr(raw)
        return SecretStr("")

    @field_validator("password_confirm", mode="before")
    @classmethod
    def transform_pw2(cls, raw: Any) -> SecretStr:
        if raw:
            return SecretStr(raw)
        return SecretStr("")

    @computed_field
    @property  # type: ignore
    def has_password(self) -> bool:
        return bool(self.password)

    @computed_field
    @property  # type: ignore
    def principal(self) -> str:
        return f"/user/{self.login}"

    def fetch_policies(self) -> List[Policy]:
        from applications.pinceau6.models.principal_policies import PrincipalPolicies

        principal_list = [self.principal, *self.groups]

        global_context = GlobalContext.get_instance()
        mongodb_handler = MongoDBHandler.from_default(global_context)

        principal_policies = mongodb_handler.load_multiples(
            PrincipalPolicies.META_MODEL, {"principal": {"$in": principal_list}}
        )

        all_policies = []
        for principal_policy in principal_policies:
            all_policies += principal_policy.policies

        return all_policies

    def validate_password(self, password: str) -> bool:
        if self.salt is None:
            raise ValueError("salt should not be None")

        hashed_password = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.salt, 100000
        )

        return self.password == hashed_password

    def set_password(self, password: str):
        self.salt = os.urandom(32)
        hashed_password = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.salt, 100000
        )

        self.password = hashed_password

    """
    def as_dict(self, include_credentials: bool = True) -> Mapping[str, Any]:
        super_value = super().as_dict(exclude=exclude)
        values = {
            **super_value,
            "_model": "user",
        }

        if include_credentials:
            values.update({"password": self._password or "", "salt": self._salt or ""})

        return values

    def to_json_dict(self: "User") -> "JSONParam":
        json_dict = self.as_dict(include_credentials=False)

        return cast("JSONParam", json_dict)

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            *Character.ui_model_fields(),
        ]
    """

    @property
    def meta_label(self):
        print(f"{self.model_fields=}")
        print(f"{self.model_computed_fields=}")
        return f"{self.display_name} ({self.login})"

    @model_validator(mode="after")
    def check_passwords(self) -> Self:
        pw0 = self.old_password
        pw1 = self.password_input
        pw2 = self.password_confirm

        if self.has_password:
            # we validate the old password even if not given!
            if (pw1 or pw2) and not self.validate_password(
                pw0.get_secret_value() or ""
            ):
                raise ValueError("bad password")

        if pw1 or pw2:
            if pw1 != pw2:
                raise ValueError("passwords do not match")

            if pw1:  # unnecessary as pw1 should be non None at this point
                self.set_password(pw1.get_secret_value())

        return self

    def before_save_handler(self, context: "Context") -> None:
        from applications.pinceau6.models.user_group import UserGroup

        super().before_save_handler(context)

        if not self.has_password and (self.password or self.password_confirm):
            if self.password != self.password_confirm:
                raise ValidationError()
            self.set

        current_groups = set(self.groups)
        previous_groups: Set[str] = set()

        mongodb_handler = MongoDBHandler.from_default(context)

        if self.id:
            previous_value = mongodb_handler.get_instance(
                self.__class__, self.__class__.META_MODEL, self.id
            )

            previous_groups = set(previous_value.groups)

        added_groups = current_groups - previous_groups
        removed_groups = previous_groups - current_groups

        added_group_objects = list(
            mongodb_handler.load_multiples(
                UserGroup.META_MODEL, {"principal": {"$in": list(added_groups)}}
            )
        )
        removed_group_objects = list(
            mongodb_handler.load_multiples(
                UserGroup.META_MODEL, {"principal": {"$in": list(removed_groups)}}
            )
        )

        for group in added_group_objects:
            add_user_to_group(context, self, group)

        for group in removed_group_objects:
            remove_user_from_group(context, self, group)
