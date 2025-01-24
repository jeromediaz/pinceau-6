from typing import Optional, List, Set, TYPE_CHECKING

from applications.pinceau6.utils import add_user_to_group, remove_user_from_group
from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler
from core.models.a_model import AModel
from ui.helper import P6ReferenceField, FieldOptions, P6Field

if TYPE_CHECKING:
    from core.context.context import Context


class UserGroup(AModel):
    META_MODEL = "p6_user_group"

    name: str
    parent_group: Optional[str] = P6ReferenceField(
        None, reference="data/mongodb/p6_user_group"
    )

    users: List[str] = P6ReferenceField(
        [], reference="data/mongodb/user", option_value="principal"
    )

    # users: List[str] = []
    principal: str = P6Field("-", options=FieldOptions.READ_ONLY)

    def as_principal(self) -> str:
        global_context = GlobalContext.get_instance()

        if self.parent_group:
            parent_user_group = self.load_reference(
                global_context, "parent_group", self.__class__
            )
            if parent_user_group:
                return f"{parent_user_group.as_principal()}/{self.name}"

        return f"/group/{self.name}"

    @property
    def meta_label(self):
        global_context = GlobalContext.get_instance()

        if self.parent_group:
            parent_user_group = self.load_reference(
                global_context, "parent_group", self.__class__
            )

            return f"{parent_user_group.meta_label}/{self.name}"

        return self.name

    def before_save_handler(self, context: "Context") -> None:
        from applications.pinceau6.models.user import User

        super().before_save_handler(context)
        self.principal = self.as_principal()

        current_users = set(self.users)
        previous_users: Set[str] = set()

        mongodb_handler = MongoDBHandler.from_default(context)

        if self.id:
            previous_value = mongodb_handler.get_instance(
                self.__class__, self.__class__.META_MODEL, self.id
            )

            previous_users = set(previous_value.users)

            # TODO: if name change, process new principal for subvalues

        added_users = current_users - previous_users
        removed_users = current_users - previous_users

        added_user_objects = mongodb_handler.load_multiples(
            User.META_MODEL, {"principal": {"$in": list(added_users)}}
        )
        removed_user_objects = mongodb_handler.load_multiples(
            User.META_MODEL, {"principal": {"$in": list(removed_users)}}
        )

        for user in added_user_objects:
            add_user_to_group(context, user, self)

        for user in removed_user_objects:
            remove_user_from_group(context, user, self)
