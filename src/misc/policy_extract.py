from typing import Dict, Set, Any, List


def _build_part_matcher(part: str):
    if part.startswith("<") and part.endswith(">"):

        def part_matcher(other_part: str) -> str | bool:
            return other_part

        return True, part_matcher

    else:

        def part_matcher(other_part: str) -> str | bool:
            return other_part == "*" or other_part == part

        return False, part_matcher


def build_policy_matcher(rule: str):

    parts = rule.split("/")
    part_matchers = []

    part_extractor_count = 0

    for part in parts:
        acc, matcher = _build_part_matcher(part)

        part_extractor_count += 1 if acc else 0
        part_matchers.append(matcher)

    def policy_matcher(resource: str) -> bool | List[Any]:

        extracted_parts: List[Any] = []

        if resource == "*":
            resource = "/".join(["*"] * len(part_matchers))

        for resource_part, matcher_part in zip(resource.split("/"), part_matchers):
            if matcher_part and not resource_part:
                return False
            if resource_part and not matcher_part:
                return extracted_parts

            part_match = matcher_part(resource_part)

            if part_match is True:
                continue
            if part_match is False:
                return False

            extracted_parts.append(part_match)
        return extracted_parts

    def matching_parts(resources: List[str]) -> str | Set[Any] | Dict[str, Any]:
        if part_extractor_count == 1:
            matched_parts_set: Set[str] = set()
            for rsc in resources:
                matched_parts = policy_matcher(rsc)

                if isinstance(matched_parts, list):
                    matched_parts_set.add(matched_parts[0])

            return "*" if "*" in matched_parts_set else matched_parts_set

        matched_parts_accumulator: List[List[str]] = []
        for rsc in resources:
            matched_parts = policy_matcher(rsc)

            if isinstance(matched_parts, list):
                matched_parts_accumulator.append(matched_parts)

        final_value: Dict[Any, Any] = {}

        for accumulated in matched_parts_accumulator:
            work_value: Dict[Any, Any] | Set[Any] = final_value
            for idx in range(part_extractor_count):
                is_last = idx + 1 == part_extractor_count
                is_before_last = idx + 2 == part_extractor_count
                part = accumulated[idx]

                if is_last:
                    if part == "*":
                        work_value.clear()
                        work_value.add("*")
                    if "*" not in work_value:
                        work_value.add(part)

                elif is_before_last:
                    work_value = work_value.setdefault(part, set())
                else:
                    work_value = work_value.setdefault(part, {})

        return final_value

    return matching_parts


def check_policy_resource_match(policy_resource: str, resource: str) -> bool:
    if policy_resource == "*":
        return True

    for policy_rsc_part, rsc_part in zip(
        policy_resource.split("/"), resource.split("/")
    ):
        if policy_rsc_part and not rsc_part:
            return False

        if not policy_rsc_part and rsc_part:
            return True

        if policy_rsc_part == "*":
            continue

        if policy_rsc_part != rsc_part:
            return False

    return True


if __name__ == "__main__":
    resources = [
        "data/mongodb/user",
        "data/mongodb/*",
        "data/mongodb/groups",
    ]

    to_check = "data/mongodb/<str:collection>"

    matcher = build_policy_matcher(to_check)

    print(matcher(resources))
