import asyncio
import types
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from flask_socketio import SocketIO


def register_websocket_event(message: Optional[str] = None):
    def my_decorator(func):
        final_message = message if message else func.__name__

        def wrapper(socket: "SocketIO", **params):
            def handler(*args):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError as e:
                    if str(e).startswith("There is no current event loop in thread"):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    else:
                        raise e

                task = loop.create_task(func(*args, **params))
                if not loop.is_running():
                    loop.run_until_complete(task)

                return task.result()
                # loop.run_until_complete(func(*args, **params))

            socket.on_event(final_message, handler)

        wrapper.is_websocket_handler = True
        return wrapper

    return my_decorator


def is_register_websocket_handler(func) -> bool:
    return isinstance(func, types.FunctionType) and getattr(
        func, "is_websocket_handler", False
    )
