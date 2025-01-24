from applications.huggingface.tasks.image_train_task import (
    ImageTrainTask,
)
from core.tasks.task_dag import TaskDAG

with TaskDAG(id="image_training"):
    # split_data = SplitData(id="split_data", requires_trained_model=False)

    # prepare_ds = ImageTrainPrepareDataset(id="prepare_ds", is_passthrough=True)

    train = ImageTrainTask(id="train")

    # split_data >> train
