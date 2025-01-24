from typing import Optional, Any, Mapping, Set

from core.context.context import Context
from core.database.mongodb import MongoDBHandler
from misc.policy_extract import build_policy_matcher, check_policy_resource_match


class UserContext(Context):
    def __init__(self, user_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        from core.context.global_context import GlobalContext

        self._user_id = user_id

        context = GlobalContext.get_instance()
        mongo_db_handler = MongoDBHandler.from_default(context)
        self._policies = None

        self.user = mongo_db_handler.load_one("user", {"_id": user_id})

    def serialize(self) -> Mapping[str, Any]:
        return {**super().serialize(), "user_id": self._user_id}

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        return cls(data["user_id"])

    @property
    def user_id(self) -> str:
        return self._user_id

    def has(self, key: str) -> bool:
        if key in {"login", "display_name", "avatar"}:
            return True

        return super().has(key)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        if key in {"login", "display_name", "avatar"}:
            return getattr(self.user, key)

        super().get(key, default)

    def set(self, key: str, value: Any):
        if key in {"login", "display_name", "avatar"}:
            setattr(self.user, "_" + key, value)

        super().set(key, value)

    @property
    def policies(self):
        policies = self._policies
        if not policies:
            policies = self.user.fetch_policies()
            self._policies = policies

        return policies

    def is_allowed(self, action: str, resource: str) -> bool:
        policies_with_action = [
            policy
            for policy in self.policies
            if action in policy.actions or "*" in policy.actions
        ]

        # TODO: handle non resource with * inside
        policies_matching = [
            policy
            for policy in policies_with_action
            if check_policy_resource_match(policy.resource, resource)
        ]

        return bool(policies_matching)

    def extract_allowed_values(
        self, action: str, rule: str
    ) -> str | Set[Any] | Mapping[Any, Any]:
        matcher = build_policy_matcher(rule)

        policies_with_action = [
            policy
            for policy in self.policies
            if action in policy.actions or "*" in policy.actions
        ]

        resources = [policy.resource for policy in policies_with_action]

        return matcher(resources)
