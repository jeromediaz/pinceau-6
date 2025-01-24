from typing import TYPE_CHECKING

from core.database.mongodb import MongoDBHandler

if TYPE_CHECKING:
    from applications.pinceau6.models.user import User
    from applications.pinceau6.models.user_group import UserGroup
    from core.context.context import Context


def add_user_to_group(context: "Context", user: "User", group: "UserGroup"):
    print(f"add_user {user} to group {group}")

    user_principal = user.as_principal()
    group_principal = group.as_principal()

    save_group = False
    save_user = False

    if user_principal not in group.users:
        group.users.append(user_principal)
        save_group = True

    if group_principal not in user.groups:
        user.groups.append(group_principal)
        save_user = True

    mongodb_handler = MongoDBHandler.from_default(context)

    if save_group:
        mongodb_handler.save_object(context, group, skip_hooks=True)

    if save_user:
        mongodb_handler.save_object(context, user, skip_hooks=True)


def remove_user_from_group(context: "Context", user: "User", group: "UserGroup"):
    print(f"remove_user {user} from group {group}")

    user_principal = user.as_principal()
    group_principal = group.as_principal()

    save_group = False
    save_user = False

    if user_principal in group.users:
        group.users.remove(user_principal)
        save_group = True

    if group_principal in user.groups:
        user.groups.remove(group_principal)
        save_user = True

    mongodb_handler = MongoDBHandler.from_default(context)

    if save_group:
        mongodb_handler.save_object(context, group, skip_hooks=True)

    if save_user:
        mongodb_handler.save_object(context, user, skip_hooks=True)
