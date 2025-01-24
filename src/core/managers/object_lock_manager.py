from typing import Set, Dict, TYPE_CHECKING

from flask_socketio import leave_room, join_room

if TYPE_CHECKING:
    from flask_socketio import SocketIO


class ObjectLockManager:

    def __init__(self) -> None:
        self._locked_object_set: Set[str] = set()
        self._sid_to_locked_objects: Dict[str, Set[str]] = {}

    def try_acquire_lock(self, sid: str, lock_id: str) -> bool:
        # TODO: add asyncio lock
        print("try_acquire_lock")
        sid_set = self._sid_to_locked_objects.setdefault(sid, set())
        if lock_id in sid_set:
            # already locked by sid
            print("> already locked by sid")
            return True
        if lock_id in self._locked_object_set:
            print(f"> already locked by other joining lock_{lock_id}")
            join_room(f"lock_{lock_id}")
            return False

        print("> getting lock")
        leave_room(f"lock_{lock_id}")

        self._locked_object_set.add(lock_id)
        sid_set.add(lock_id)
        return True

    def has_lock(self, sid: str, lock_id: str) -> bool:
        sid_set = self._sid_to_locked_objects.setdefault(sid, set())
        return lock_id in sid_set

    def release_lock(self, websocket: "SocketIO", sid: str, lock_id: str) -> bool:
        print("releaseLock")
        if not self.has_lock(sid, lock_id):
            print("false")
            return False

        self.emit_release(websocket, lock_id)

        self._sid_to_locked_objects[sid].remove(lock_id)
        self._locked_object_set.remove(lock_id)
        print("true")
        return True

    def release_all_locks(self, websocket: "SocketIO", sid: str):
        sid_set = self._sid_to_locked_objects.setdefault(sid, set())

        # TODO: send WS event to say lock was released

        self._locked_object_set = self._locked_object_set - sid_set
        sid_set.clear()
        for lock_id in sid_set:
            self.emit_release(websocket, lock_id)
            leave_room(f"lock_{lock_id}", sid)

    def emit_release(self, websocket: "SocketIO", lock_id: str):
        print(f"emit_release {lock_id=}")
        websocket.emit("lockChange", {lock_id: "released"}, to=f"lock_{lock_id}")
