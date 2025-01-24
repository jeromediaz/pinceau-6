from typing import Optional

import flask


class WebsocketAuthManager:
    def __init__(self):
        self._sid_map = dict()

    def is_registered(self, sid: Optional[str] = None):
        session_id = sid if sid else flask.request.sid  # type: ignore

        return session_id in self._sid_map

    def get_user_data(self):
        session_id = getattr(flask.request, "sid")

        return self._sid_map.get(session_id)

    def set_user_data(self, data):
        session_id = getattr(flask.request, "sid")

        self._sid_map[session_id] = data

    def remove_user_data(self):
        session_id = getattr(flask.request, "sid")
        if session_id in self._sid_map:
            del self._sid_map[session_id]
