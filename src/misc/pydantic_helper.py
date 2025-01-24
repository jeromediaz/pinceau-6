import types
from typing import Tuple, get_origin, Union, Any, get_args, Dict, TYPE_CHECKING

from flask import make_response, jsonify, abort
from pydantic import ValidationError
from pydantic.fields import FieldInfo, ComputedFieldInfo
from pydantic_core import PydanticUndefined

if TYPE_CHECKING:
    import typing_extensions as te


def extract_main_type(field_type: type) -> Tuple[type, bool]:
    field_origin = get_origin(field_type)

    multiple = field_origin is list or field_origin is set

    if not multiple and hasattr(field_type, "__origin__"):
        multiple = field_type.__origin__ is list or field_type.__origin__ is set

    main_type = field_type
    if multiple:
        args = get_args(field_type)
        main_type = args[0]

    return main_type, multiple


def extract_computed_type_origin(
    computed_field_info: ComputedFieldInfo,
) -> Tuple[type, bool, bool, Any]:
    field_origin = get_origin(computed_field_info.return_type)

    simple_origin = field_origin is not Union and field_origin is not types.UnionType

    default = None  # we can't have a default value for a computed field

    if simple_origin:
        if not computed_field_info.return_type:
            raise ValueError("no field annotation")
        main_type, multiple = extract_main_type(computed_field_info.return_type)

        if not main_type:
            raise ValueError("unsupported values")

        return main_type, False, multiple, default

    args = get_args(computed_field_info.return_type)
    args_len = len(args)

    if args_len == 1:
        raise ValueError("unsupported values")

    # main_type is processed from first arg only
    main_type, multiple = extract_main_type(args[0])

    last_arg = args[-1]
    # optional flag is processed from last arg
    optional = last_arg is types.NoneType

    default = None

    return main_type, optional, multiple, default


def extract_type_origin(field_info: FieldInfo) -> Tuple[type, bool, bool, Any]:
    field_annotation = field_info.annotation
    field_origin = get_origin(field_annotation)

    simple_origin = field_origin is not Union and field_origin is not types.UnionType

    default = (
        field_info.default if field_info.default is not PydanticUndefined else None
    )

    if simple_origin:
        if not field_annotation:
            raise ValueError("no field annotation")
        main_type, multiple = extract_main_type(field_annotation)

        if not main_type:
            raise ValueError("unsupported values")

        return main_type, False, multiple, default

    args = get_args(field_info.annotation)
    args_len = len(args)

    if args_len == 1:
        raise ValueError("unsupported values")

    # main_type is processed from first arg only
    main_type, multiple = extract_main_type(args[0])

    last_arg = args[-1]
    # optional flag is processed from last arg
    optional = last_arg is types.NoneType

    default = (
        field_info.default if field_info.default is not PydanticUndefined else None
    )

    return main_type, optional, multiple, default

    # TODO: handle complex cases


def flask_abort_pydantic_error(error: ValidationError) -> "te.NoReturn":
    field_errors: Dict[int | str, Any] = {}
    for detail_error in error.errors():
        print(f"{detail_error=} {type(detail_error)=}")
        work_dict = field_errors
        error_loc_list = list(detail_error["loc"])
        if not error_loc_list:
            field_errors["root"] = {"serverError": detail_error["msg"]}
            continue
        for path in error_loc_list[:-1]:
            work_dict = work_dict.setdefault(path, {})

        work_dict[error_loc_list[-1]] = detail_error["msg"]

    abort(make_response(jsonify({"errors": {**field_errors}}), 400))
