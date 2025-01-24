import json
from typing import TypeAlias

from flask import request

Range: TypeAlias = tuple[int, int]


def get_range() -> Range:
    range_str = request.args.get("range")

    if range_str:
        start_str, end_str = range_str[1:-1].split(",")
        return int(start_str), int(end_str)

    return 0, 25


def get_filters():
    filter_arg = request.args.get("filter")

    if not filter_arg:
        return {}

    return json.loads(filter_arg)


def get_sort():
    sort_arg = request.args.get("sort")

    if not sort_arg:
        return None, None

    key, order = json.loads(sort_arg)
    reverse = True if order == "DESC" else False

    return key, reverse
