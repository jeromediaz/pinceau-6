from typing import TYPE_CHECKING, Mapping, Any, List

from flask import jsonify

from api.blueprint_decorator import register_route, action_required
from api.security_wrapper import authentication
from core.context.global_context import GlobalContext
from core.context.user_context import UserContext
from core.database.mongodb import MongoDBHandler

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext
    from flask import Response


@register_route("")
@authentication()
@action_required("view", "api/menu")
def menu(context: "CompositeContext") -> "Response":

    user_context = context.cast_as(UserContext)
    global_context = context.cast_as(GlobalContext)

    models_manager = global_context.models_manager

    allowed_values = user_context.extract_allowed_values(
        "list", "data/<provider>/<collection>"
    )

    resource_list: List[Mapping[str, Any]] = [
        {
            "type": "resource-item",
            "name": "user",
            "primaryText": "Users",
            "provider": "mongodb",
            "categories": ["/system/users/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "chat",
            "primaryText": "Chat",
            "provider": "mongodb",
            "categories": ["/"],
            "leftIcon": "chat",
        },
        {
            "type": "resource-item",
            "name": "test_subquery",
            "primaryText": "Test Subquery",
            "provider": "mongodb",
            "categories": ["/eurelis/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "llamaindex_llm",
            "primaryText": "LI-LLM",
            "provider": "mongodb",
            "categories": ["/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "resource",
            "primaryText": "Resource",
            "provider": "mongodb",
            "categories": ["/system/resources/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "page_eurelis",
            "primaryText": "Page Eurelis",
            "provider": "mongodb",
            "categories": ["/eurelis/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "dag_persisted",
            "primaryText": "DAG Persisted",
            "provider": "mongodb",
            "categories": ["/system/dag/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "graphviz",
            "primaryText": "Graphviz",
            "provider": "mongodb",
            "categories": ["/test/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "training_finetuning_sequence_classification",
            "primaryText": "Model training",
            "provider": "mongodb",
            "categories": ["/saaswedo/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "mongo_facet",
            "primaryText": "MongoFacet",
            "provider": "mongodb",
            "categories": ["/", "/saaswedo/"],
            "leftIcon": "list_outlined",
        },
        {
            "type": "resource-item",
            "name": "llamaindex_index",
            "primaryText": "LI-Index",
            "provider": "mongodb",
            "categories": ["/"],
            "leftIcon": "list_outlined",
        },
    ]

    for resource in resource_list:
        resource_model = models_manager.get_model(resource.get("name"))
        resource["categories"] = resource.get("categories") or ["/"]

        if resource_model:
            resource["categories"].extend(resource_model.categories)

    mongo_db_handler = MongoDBHandler.from_default(context)

    other_resources = mongo_db_handler.load_multiples("resource", {})

    other_resources_list = [data for data in (row.as_dict() for row in other_resources)]
    other_resource_extract = (
        {
            "type": "resource-item",
            "name": data.get("name"),
            "primaryText": data.get("label"),
            "provider": data.get("provider", "mongodb"),
            "categories": (
                (data.get("categories") or ["/"])
                + models_manager.get_model(data.get("name")).categories
                if models_manager.get_model(data.get("name"))
                else []
            ),
            "leftIcon": data.get("left_icon", "list-outlined"),
        }
        for data in other_resources_list
    )

    resource_list.extend(other_resource_extract)
    resources = sorted(resource_list, key=lambda r: r["primaryText"].lower())

    #  TODO: put the filter into a function
    if "*" in allowed_values:
        if "*" not in allowed_values["*"]:
            resources = [
                resource
                for resource in resources
                if resource["name"] in allowed_values["*"]
            ]
    else:
        resources = [
            resource
            for resource in resources
            if resource["provider"] in allowed_values
            and (
                resource["name"] in allowed_values[resource["provider"]]
                or "*" in allowed_values[resource["provider"]]
            )
        ]

    menu_tree = [
        {
            "type": "application_selector",
            "choices": global_context.applications_manager.tag_name_map
        },
        {"type": "dashboard"},
        {
            "type": "item",
            "to": "/dag",
            "primaryText": "DAGs",
            "leftIcon": "account_tree",
        },
        {
            "type": "item",
            "to": "/jobs",
            "primaryText": "Jobs",
            "leftIcon": "work_history",
        },
        {
            "type": "collapse",
            "primaryText": "Resources",
            "leftIcon": "format-list-bulleted",
            "rightIcon": ["expand_more", "expand_less"],
            "content": resources,
        },
    ]

    return jsonify(menu_tree)
