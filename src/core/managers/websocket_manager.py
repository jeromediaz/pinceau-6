import os
from inspect import getmembers
from typing import TYPE_CHECKING

from api.websocket_decorator import is_register_websocket_handler
from core.managers.websocket_auth_manager import WebsocketAuthManager

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext
    from flask_socketio import SocketIO


class WebsocketManager:

    def __init__(self, websocket: "SocketIO", context: "GlobalContext") -> None:
        self.websocket = websocket
        self.context = context
        self.websocket_auth_manager = WebsocketAuthManager()

    def register_handlers_in_folder(self, module_prefix: str, folder: str) -> None:
        if not os.path.isdir(folder):
            return

        for file in os.listdir(folder):
            if not file.endswith("_handlers.py"):
                continue

            file_name, _ = os.path.splitext(file)
            module_name = f"{module_prefix}.{file_name}"

            module = __import__(module_name, fromlist=[""])
            functions = getmembers(module, is_register_websocket_handler)

            if not functions:
                continue

            for register_handler in functions:
                register_handler[1](
                    self.websocket,
                    context=self.context,
                    websocket=self.websocket,
                    websocket_auth_manager=self.websocket_auth_manager,
                )

    def register_handlers(self) -> None:
        folder = os.path.join(os.path.dirname(__file__), "../websocket")

        self.register_handlers_in_folder("core.websocket", folder)
