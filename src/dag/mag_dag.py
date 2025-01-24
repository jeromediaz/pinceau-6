from core.tasks.task_dag import TaskDAG
from tasks.agent_mongodb_upsert import AgentMongoDBUpsert
from tasks.magnetic_declination_task import MagneticDeclinationTask
from tasks.range_task import RangeTask
from tasks.round_robin_task import RoundRobinTask

with TaskDAG(id="mag") as dag:
    declination_task = MagneticDeclinationTask()
    mongodb = AgentMongoDBUpsert()

    declination_task >> mongodb

with TaskDAG(id="range_mag"):
    lat_task = RangeTask(
        varname="latitude", start=-90, end=90, label="Latitude", id="lat_range"
    )
    lng_task = RangeTask(
        varname="longitude", start=-180, end=180, label="Longitude", id="lng_range"
    )
    round_robin = RoundRobinTask(id="round_robin")
    geo_task_1 = MagneticDeclinationTask(id="geo_task_1")
    geo_task_2 = MagneticDeclinationTask(id="geo_task_2")

    mongodb_1 = AgentMongoDBUpsert(id="mongodb_1")
    mongodb_2 = AgentMongoDBUpsert(id="mongodb_2")

    lat_task >> lng_task >> round_robin
    round_robin >> geo_task_1 >> mongodb_1
    round_robin >> geo_task_2 >> mongodb_2
