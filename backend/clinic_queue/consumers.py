from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .realtime import QUEUE_GROUP
from .services import queue_payload


class QueueConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(QUEUE_GROUP, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                'type': 'queue.snapshot',
                'payload': await database_sync_to_async(queue_payload)(),
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(QUEUE_GROUP, self.channel_name)

    async def queue_update(self, event):
        await self.send_json(
            {
                'type': 'queue.update',
                'payload': event['payload'],
            }
        )
