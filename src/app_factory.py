from typing import Optional, cast, Type

from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS
from flask_socketio import SocketIO

from celery_factory import celery_factory
from conf import Config
from core.context.global_context import GlobalContext
from misc.functions import strtobool
from misc.mongo_json_encoder import MongoEncoder


def flask_app_factory(
    app_name: Optional[str] = None, context: Optional[GlobalContext] = None
) -> Flask:
    flask_app_name = app_name or __name__

    config = Config()
    global_context = context or GlobalContext()

    app = Flask(
        flask_app_name,
        static_url_path="/admin",
        static_folder="../etc/admin/pinceau6/dist",
    )

    app.json_encoder = cast(Type[JSONEncoder], MongoEncoder)
    app.config["CORS_EXPOSE_HEADERS"] = ["Content-Range"]
    app.config["SECRET_KEY"] = config.get("FLASK_SECRET_KEY")

    allowed_origins = config.get(
        "ALLOWED_ORIGINS", default="http://localhost:8000"
    ).split(";")

    celery_disabled = strtobool(config.get("CELERY_DISABLED", default="False"))

    CORS(app, supports_credentials=True)
    socketio = SocketIO(
        app,
        async_mode="threading",
        cors_allowed_origins=allowed_origins,
        message_queue=config["CELERY_BROKER_URL"],
    )

    global_context.set_websocket(socketio)

    if not celery_disabled:
        global_context.set_celery_client(celery_factory())

    return app
