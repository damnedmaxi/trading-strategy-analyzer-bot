from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BotStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.bot_id = self.scope["url_route"]["kwargs"]["bot_id"]
        self.group_name = f"bot_{self.bot_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # No inbound messages expected yet, but we log them for debugging.
        await self.send_json({"type": "echo", "payload": content})

    async def bot_update(self, event):
        await self.send_json(event["payload"])
