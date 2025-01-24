from core.context.global_context import GlobalContext


global_context = GlobalContext()


mongo = global_context.dbms["mongodb_mm1"]
