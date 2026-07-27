"""SSE subscription manager — fan-out events to connected clients."""

import asyncio
import json
from app.observability.logging import logger


class SSEManager:
    """Manages SSE subscriptions per interview_id.

    Events published via publish() are fanned out to every subscriber
    queue for that interview.  Subscribers are identified by a unique
    subscriber_id; unsubscribe() removes a single subscriber.
    """

    def __init__(self):
        self._subscriptions: dict[str, dict[str, asyncio.Queue]] = {}

    async def subscribe(self, interview_id: str, subscriber_id: str) -> asyncio.Queue:
        """Create a queue for *subscriber_id* and return it."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        if interview_id not in self._subscriptions:
            self._subscriptions[interview_id] = {}
        self._subscriptions[interview_id][subscriber_id] = queue
        logger.debug("sse_subscribe", interview_id=interview_id, subscriber_id=subscriber_id)
        return queue

    async def unsubscribe(self, interview_id: str, subscriber_id: str):
        """Remove subscriber and clean up empty interview entries."""
        subs = self._subscriptions.get(interview_id, {})
        subs.pop(subscriber_id, None)
        if not subs:
            self._subscriptions.pop(interview_id, None)
        logger.debug("sse_unsubscribe", interview_id=interview_id, subscriber_id=subscriber_id)

    async def publish(self, interview_id: str, event: dict):
        """Publish *event* to every subscriber of *interview_id*.

        Slow / disconnected subscribers are skipped (non-blocking put).
        """
        subs = self._subscriptions.get(interview_id, {})
        if not subs:
            return
        dead: list[str] = []
        payload = json.dumps(event, ensure_ascii=False)
        for sid, queue in subs.items():
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(sid)
                logger.warning("sse_queue_full", interview_id=interview_id, subscriber_id=sid)
        for sid in dead:
            await self.unsubscribe(interview_id, sid)


# Module-level singleton — import this everywhere.
sse_manager = SSEManager()
