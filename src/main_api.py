import asyncio
import atexit
import logging
import sys
import threading

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import redirect

from app_factory import flask_app_factory
from applications.pinceau6.models.user import User
from conf.config import Config
from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler
from core.utils import load_dag_folder, load_local_application
from dag.story_dag import story_dag
from misc.functions import strtobool

logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.DEBUG)


def create_app():
    app = flask_app_factory(__name__)
    GlobalContext.get_instance().set_flask_app(app)

    @app.cli.command("init")
    def init_pinceau():
        global_context_instance = GlobalContext.get_instance()
        db_handler = MongoDBHandler.from_default(global_context_instance)
        if not db_handler.load_one("user", {"login": "admin"}):
            admin_user = User(login="admin", uid="admin", display_name="Administrator")
            admin_user.set_password("admin")
            db_handler.save_object(global_context_instance, admin_user, "user")

    is_3_12 = sys.version_info >= (3, 12)

    loop = None

    if is_3_12:
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=loop.run_forever)

    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.start()

    if is_3_12:
        thread.start()

    atexit.register(lambda: scheduler.shutdown(wait=False))

    @app.route("/", methods=["GET"])
    def redirect_admin():
        return redirect("/admin/index.html", code=302)

    load_dag_folder("dag", "dag")

    load_local_application("pinceau6")
    load_local_application("arxiv")
    load_local_application("chat")
    load_local_application("huggingface")
    load_local_application("llama_index")
    load_local_application("mangafox")
    load_local_application("inproj")
    load_local_application("pinceau6_web")

    global_context = GlobalContext.get_instance()
    global_context.set_scheduler(scheduler)

    story_dag()
    return app


if __name__ == "__main__":
    config = Config()
    app = create_app()
    debug = strtobool(config.get("FLASK_DEBUG", default="False"))

    app.run(debug=debug, port=8000, host="0.0.0.0", use_evalex=False)
