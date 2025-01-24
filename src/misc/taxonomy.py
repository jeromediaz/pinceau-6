from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Permission(Enum):
    allowed = 1
    unset = 0
    forbidden = -1


class TaxonomyPermissions(BaseModel):
    taxonomy: str
    can_read: Permission = Permission.unset
    can_write: Permission = Permission.unset
    can_execute: Permission = Permission.unset


def merge_permissions(old_value: Permission, compare_value: Permission) -> Permission:
    if compare_value == Permission.unset:
        return old_value

    return compare_value


def get_rights(
    taxonomy: str, taxonomy_permissions: List[TaxonomyPermissions]
) -> Optional[TaxonomyPermissions]:

    filtered_permissions = [
        permission
        for permission in taxonomy_permissions
        if taxonomy.startswith(permission.taxonomy)
    ]

    if not filtered_permissions:
        return None

    sorted_permissions = sorted(
        filtered_permissions, key=lambda permission: len(permission.taxonomy)
    )

    can_read = Permission.unset
    can_write = Permission.unset
    can_execute = Permission.unset

    for sorted_permission in sorted_permissions:
        can_read = merge_permissions(can_read, sorted_permission.can_read)
        can_write = merge_permissions(can_write, sorted_permission.can_write)
        can_execute = merge_permissions(can_execute, sorted_permission.can_execute)

    last_taxonomy = sorted_permissions[-1].taxonomy

    return TaxonomyPermissions(
        taxonomy=last_taxonomy,
        can_read=can_read,
        can_write=can_write,
        can_execute=can_execute,
    )
