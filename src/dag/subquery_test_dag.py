import json

from llama_index.core.schema import QueryBundle
from llama_index.core.tools import ToolMetadata
from llama_index.llms.openai import OpenAI
from llama_index.question_gen.openai.base import OpenAIQuestionGenerator

from core.tasks.task_dag import TaskDAG
from tasks.mongo_object_task import MongoObjectTask


def mongo_handler(task, context, *, model_object, **kwargs):
    context.task_data(
        task,
        "result",
        "-",
    )

    tool_metadatas = list(
        map(
            lambda tool: ToolMetadata(
                name=tool.get("name"), description=tool.get("description")
            ),
            model_object.tools,
        )
    )

    tools_dict = dict()
    for tool in tool_metadatas:
        tools_dict[tool.name] = tool.description

    database = context.get_dbms("mongodb")["pinceau6"]

    collection = database["test_subquery_task_result"]

    result_list = list()

    for model in model_object.models:
        question_generator = OpenAIQuestionGenerator.from_defaults(
            llm=OpenAI(
                model=model,
                temperature=0,
                api_key="",  # FIXME
            )
        )

        for question in model_object.questions:
            sub_questions = question_generator.generate(
                tool_metadatas, QueryBundle(query_str=question)
            )

            sub_question_array = list(
                map(
                    lambda sub_question: {
                        "tool": sub_question.tool_name,
                        "question": sub_question.sub_question,
                    },
                    sub_questions,
                )
            )

            result = {
                "question": question,
                "model": model,
                "tools": tools_dict,
                "sub_questions": sub_question_array,
                "temperature": 0,
            }

            result_list.append(
                {
                    "question": question,
                    "model": model,
                    "sub_questions": sub_question_array,
                }
            )

            as_str = json.dumps(result_list, indent=4)
            context.task_data(
                task,
                "result",
                as_str,
            )

            collection.insert_one(result)

    return {"results": result_list}


with TaskDAG(id="subquery_test_dag") as dag:
    MongoObjectTask("test_subquery", handler=mongo_handler, id="mongo_object_task")
