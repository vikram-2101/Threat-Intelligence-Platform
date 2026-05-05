import json
from typing import Any, Dict
from redis.asyncio import Redis
from app.core.config import settings

class RedisManager:
    def __init__(self, url: str):
        self.client = Redis.from_url(
            url, 
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0
        )

    async def publish_event(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publishes a JSON-encoded message to a Redis channel.
        """
        await self.client.publish(channel, json.dumps(message))

# Global Redis manager instance
redis_manager = RedisManager(settings.REDIS_URL)

async def publish_indicator_created(indicator_id: str, itype: str, value: str) -> None:
    """
    Helper to emit the indicator.created event for downstream consumers.
    """
    await redis_manager.publish_event(
        "indicator.created",
        {
            "indicator_id": indicator_id,
            "type": itype,
            "value": value
        }
    )
