import os
import pathlib

from applications.pinceau6.models.user import User
from core.context.global_context import GlobalContext
from core.models.a_model import AModel
from core.utils import load_dag_folder, load_local_application
from ui.helper import available_dag_for_model, ui_fields_from_base_model

os.environ["P6_LOAD_PERSIST_MODELS"] = "False"
os.environ["P6_RUN_MODE"] = "TEST"

os.chdir(os.path.join(pathlib.Path(__file__).parent, "../src"))
global_context = GlobalContext.get_instance()
load_dag_folder("dag", "dag")
load_local_application("mangafox")
load_local_application("arxiv")
load_local_application("huggingface")
load_local_application("pinceau6")


def test_amodel_schema():
    model_definition = global_context.models_manager.get_model("amodel")

    assert model_definition is not None

    model_class = model_definition.cls

    assert model_class is AModel, "amodel definition should be an AModel"

    available_dag_list = available_dag_for_model(model_definition.name, global_context)

    assert len(available_dag_list) == 0, "amodel shouldn't have any action associated"
    assert model_class.IS_ABSTRACT

    assert len(model_class.ui_model_fields()) == 0
    assert model_class.ui_model_layout() == "simple"

    print(model_definition.categories)


def test_user_schema_schema():
    model_definition = global_context.models_manager.get_model("user")

    assert model_definition is not None

    model_class = model_definition.cls

    assert model_class is User, "user definition should be User"

    available_dag_list = available_dag_for_model(model_definition.name, global_context)

    assert len(available_dag_list) == 0, "user shouldn't have any action associated"
    assert not model_class.IS_ABSTRACT

    assert len(model_class.ui_model_fields()) == 9
    assert model_class.ui_model_layout() == "simple"

    pydantic_ui_model_fields = ui_fields_from_base_model(model_class)

    assert model_class.ui_model_fields() == pydantic_ui_model_fields


def test_mangafox_manga_schema():
    model_definition = global_context.models_manager.get_model("mangafox_manga")

    assert model_definition is not None

    model_class = model_definition.cls

    pydantic_ui_model_fields = ui_fields_from_base_model(model_class)

    assert model_class.ui_model_fields() == pydantic_ui_model_fields


def test_training_eval_dataset_mongodb_cat_provider_schema():
    model_definition = global_context.models_manager.get_model(
        "training_eval_dataset_mongodb_cat_provider"
    )

    assert model_definition is not None

    model_class = model_definition.cls

    pydantic_ui_model_fields = ui_fields_from_base_model(model_class)

    assert model_class.ui_model_fields() == pydantic_ui_model_fields


def test_training_finetuning_sequence_classification_schema():

    model_definition = global_context.models_manager.get_model(
        "training_finetuning_sequence_classification"
    )

    assert model_definition is not None

    model_class = model_definition.cls

    pydantic_ui_model_fields = ui_fields_from_base_model(model_class)

    assert model_class.ui_model_fields() == pydantic_ui_model_fields


def test_trained_finetuning_sequence_classification_schema():

    model_definition = global_context.models_manager.get_model(
        "trained_finetuning_sequence_classification"
    )

    assert model_definition is not None

    model_class = model_definition.cls

    pydantic_ui_model_fields = ui_fields_from_base_model(model_class)

    assert model_class.ui_model_fields() == pydantic_ui_model_fields


def test_graphviz_dict():
    model_definition = global_context.models_manager.get_model("graphviz")

    assert model_definition is not None

    model_class = model_definition.cls

    pydantic_ui_model_fields = ui_fields_from_base_model(model_class)

    assert model_class.ui_model_fields() == pydantic_ui_model_fields

    model_object = model_class(name="test", dot="digraph test { a }")

    model_object_keys = model_object.as_dict().keys()

    assert len(model_object_keys) == 4

    assert "_model" in model_object_keys
    assert "_meta" in model_object_keys
    assert "dot" in model_object_keys
    assert "name" in model_object_keys

    dump_value = model_object.dump_as_map()
    assert len(dump_value.keys()) == 4
    assert "id" not in dump_value
    # assert dump_value['id'] is None
    assert "_model" in dump_value
    assert dump_value["_model"] == "graphviz"
    assert "name" in dump_value
    assert dump_value["name"] == "test"
    assert "dot" in dump_value
    assert dump_value["dot"] == "digraph test { a }"

    assert "_meta" in dump_value
    meta = dump_value["_meta"]
    assert "label" in meta
    assert meta["label"] == "test"
