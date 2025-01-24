import re
from collections import OrderedDict
from enum import Enum
from typing import Iterable, Optional, Tuple, TypeVar, Generic, Any, List

from core.tasks.graph_element import GraphElement

GraphElementClass = TypeVar("GraphElementClass", bound=GraphElement)


def none_check_factory(key: str, reverse: bool = False):
    if reverse:

        def not_none_check(item):
            return getattr(item, key) is not None

        return not_none_check

    def none_check(item):
        return getattr(item, key) is None

    return none_check


def simple_equality_check_factory(key: str, value: Any, reverse: bool = False):

    if reverse:

        def not_equal_check(item):
            item_value = getattr(item, key)
            if isinstance(item_value, Enum):
                return item_value.name != value and item_value.value != value
            return item_value != value

        return not_equal_check

    def equality_check(item):
        item_value = getattr(item, key)
        if isinstance(item_value, Enum):
            return item_value.name == value or item_value.value == value
        return item_value == value

    return equality_check


def multiple_equality_check_factory(key: str, values: List[Any], reverse: bool = False):
    filter_values_set = set(values)

    if reverse:

        def not_equal_check(item):
            # TODO: handle if item is
            return not (getattr(item, key) & filter_values_set)

        return not_equal_check

    def equality_check(item):
        return getattr(item, key) & filter_values_set

    return equality_check


def simple_in_check_factory(key: str, value: Any, reverse: bool = False):

    if reverse:

        def not_equal_check(item):
            return value not in getattr(item, key)

        return not_equal_check

    def equality_check(item):
        return value in getattr(item, key)

    return equality_check


def multiple_in_check_factory(key: str, values: List[Any], reverse: bool = False):
    filter_values_set = set(values)

    if reverse:

        def not_equal_check(item):
            return not (getattr(item, key) & filter_values_set)

        return not_equal_check

    def equality_check(item):
        return getattr(item, key) & filter_values_set

    return equality_check


class GraphElementManager(Generic[GraphElementClass]):
    def __init__(self) -> None:
        self._map: dict[str, GraphElementClass] = OrderedDict()

    def get(self, id_: str) -> Optional[GraphElementClass]:
        return self._map.get(id_)

    def __getitem__(self, id_: str) -> GraphElementClass:
        return self._map[id_]

    def __setitem__(self, id_: str, value: GraphElementClass):
        self._map[id_] = value

    def __delitem__(self, id_: str):
        del self._map[id_]

    def __contains__(self, id_: str) -> bool:
        return id_ in self._map

    def values(
        self,
        filters: Optional[dict],
        orders: Optional[Tuple[Optional[str], Optional[bool]]],
    ) -> Iterable[GraphElementClass]:
        list_values: List[GraphElementClass] = list(self._map.values())
        values: Iterable[GraphElementClass] = list_values

        if not list_values:
            # early exit
            return []

        first_value = list_values[0]

        if not filters:
            filters = {}

        for key, value in filters.items():
            is_reversed = key.startswith("-")
            final_key = key[1:] if is_reversed else key

            if not hasattr(first_value, final_key):
                continue

            value_is_list = isinstance(getattr(first_value, final_key), list)

            if value is None:
                filter_function = none_check_factory(final_key, is_reversed)
            elif isinstance(value, list):
                filter_function = multiple_equality_check_factory(
                    final_key, value, is_reversed
                )
            else:
                if value_is_list:
                    filter_function = simple_in_check_factory(
                        final_key, value, is_reversed
                    )
                else:
                    filter_function = simple_equality_check_factory(
                        final_key, value, is_reversed
                    )

            values = filter(filter_function, values)

        q = filters.get("q")
        if q:
            values = filter(
                lambda item: q in item.label or q in item.description or q in item.id,
                values,
            )

        if not values:
            return values

        if orders:
            key, reverse = orders
            if key and reverse is not None:
                if hasattr(first_value, key):
                    values = sorted(
                        values, key=lambda val: getattr(val, key), reverse=reverse
                    )
                else:
                    pattern = re.compile(r"(?<!^)(?=[A-Z])")
                    name = pattern.sub("_", key).lower()
                    if name != key and hasattr(first_value, name):
                        values = sorted(
                            values,
                            key=lambda val: getattr(val, name) or "",
                            reverse=reverse,
                        )

        return values
