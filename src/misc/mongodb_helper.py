from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context.context import Context


def mongodb_database(context: "Context", db_link: str, db_name: str):
    """
    Helper function to get a mongodb database from the context

    Args:
        context:
        db_link:
        db_name:

    Returns:

    """
    from core.context.global_context import GlobalContext
    from core.context.composite_context import CompositeContext

    if isinstance(context, GlobalContext):
        global_context = context
    elif isinstance(context, CompositeContext):
        global_context = context.cast_as(GlobalContext)
    else:
        raise ValueError(
            f"mongo_collection, bad context parameter, use an instance of GlobalContext or CompositeContext, {type(context)} given"
        )

    dbms = global_context.dbms[db_link]
    return dbms[db_name]


def mongodb_collection(
    context: "Context", db_link: str, db_name: str, collection_name: str
):
    """
    Helper function to get a mongodb collection from the context

    Args:
        context:
        db_link:
        db_name:
        collection_name:

    Returns:

    """
    mongo_database = mongodb_database(context, db_link, db_name)
    return mongo_database[collection_name]
