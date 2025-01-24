import os
import pathlib

from core.context.global_context import GlobalContext
from core.utils import load_dag_folder, load_local_application

os.environ["P6_LOAD_PERSIST_MODELS"] = "False"
os.environ["P6_RUN_MODE"] = "TEST"

os.chdir(os.path.join(pathlib.Path(__file__).parent, "../src"))
global_context = GlobalContext.get_instance()
load_dag_folder("dag", "dag")
load_local_application("arxiv")
load_local_application("huggingface")
load_local_application("chat")


def test_dag_actions_check_chat_compatible_test_model():

    model = "trained_finetuning_sequence_classification"

    model_definition = global_context.models_manager.get_model(model, False)

    assert model_definition is not None
    available_dag_list = global_context.models_manager.get_model_available_dag(
        global_context.dag_manager, model_definition.name
    )

    assert len(available_dag_list) == 3, "Three models should be available"



def test_dag_actions_training_finetuning_sequence_classification():

    model = "training_finetuning_sequence_classification"

    model_definition = global_context.models_manager.get_model(model, False)

    assert model_definition is not None

    available_dag_list = global_context.models_manager.get_model_available_dag(
        global_context.dag_manager, model_definition.name
    )

    assert len(available_dag_list) == 1, "Only training should be available"


def test_dag_actions_trained_finetuning_sequence_classification():

    model = "trained_finetuning_sequence_classification"

    model_definition = global_context.models_manager.get_model(model, False)

    assert model_definition is not None

    available_dag_list = global_context.models_manager.get_model_available_dag(
        global_context.dag_manager, model_definition.name
    )

    assert len(available_dag_list) == 3, "Training, title and evaluation should be available"
