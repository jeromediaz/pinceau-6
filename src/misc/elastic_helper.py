from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context.context import Context


def elasticsearch_client(context: "Context", db_link: str):
    """
    Helper function to get a elasticsearch index from the context

    Args:
        context:
        db_link:
        index_name:

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

    return global_context.dbms[db_link]
