import asyncio
import uuid
import weakref
from typing import Any, Optional


class AsyncEventManager:

    def __init__(self) -> None:
        self._event_map_lock = asyncio.Lock()
        self._event_map_result: dict[str, Any] = {}
        self._event_map_event: dict[str, asyncio.Event] = {}

    async def value(self, event_id: str) -> Optional[Any]:
        async with self._event_map_lock:
            if event_id in self._event_map_result:
                result = self._event_map_result[event_id]
                return result

            if event_id not in self._event_map_event:
                event = asyncio.Event()
                self._event_map_event[event_id] = event
            else:
                event = self._event_map_event[event_id]

        await event.wait()
        async with self._event_map_lock:
            result = self._event_map_result[event_id]
        return result

    def value_received(self, event_id: str, value: Any) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_value_received(event_id, value))
        loop.close()

    async def async_value_received(self, event_id: str, value: Any):
        async with self._event_map_lock:
            event = self._event_map_event.get(event_id, None)
            self._event_map_result[event_id] = value

        if event:
            event.set()

    def forgot_event(self, event_uuid: str) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_forgot_event(event_uuid))
        loop.close()

    async def async_forgot_event(self, event_uuid: str) -> None:
        async with self._event_map_lock:
            self._event_map_event.pop(event_uuid, None)
            self._event_map_result.pop(event_uuid)

    def clear(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_clear())
        loop.close()

    async def async_clear(self) -> None:
        async with self._event_map_lock:
            self._event_map_event.clear()
            self._event_map_result.clear()


class AsyncEvent:
    def __init__(self, manager: AsyncEventManager, event_id: Optional[str] = None):
        self._id = event_id if event_id else str(uuid.uuid4())
        self._manager = weakref.ref(manager)

    @property
    def id(self) -> str:
        return self._id

    async def val(self) -> Any:
        manager = self._manager()
        if manager:
            return await manager.value(self._id)

        return None
