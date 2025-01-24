from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from celery import Celery


def celery_factory() -> "Celery":
    from conf import Config
    from celery import Celery

    config = Config()

    queues = config.get("WORKER_TAGS", default="celery").split(";")
    print("=======")
    print(queues)

    task_queues = {queue: {"exchange": queue, "routing_key": queue} for queue in queues}

    print(task_queues)

    return Celery(
        main=config["CELERY_MAIN"],
        broker=config["CELERY_BROKER_URL"],
        backend=config["MONGODB_URI"],
        task_queues=task_queues,
        config_source={"broker_channel_error_retry": True},
    )
