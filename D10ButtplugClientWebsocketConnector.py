import asyncio
import json
import logging
import sys
from typing import Optional

import websockets
from buttplug.client import ButtplugClientConnector, ButtplugClientConnectorError
from buttplug.core import ButtplugMessage
from websockets.exceptions import ConnectionClosedError


class D10ButtplugClientWebsocketConnector(ButtplugClientConnector):

    def __init__(self, addr: str):
        super().__init__()
        self.addr: str = addr
        self.ws: Optional[websockets.WebSocketClientProtocol]

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.addr)
        except ConnectionRefusedError as e:
            raise ButtplugClientConnectorError(e)
        self._connected = True
        asyncio.create_task(self._consumer_handler(), name="consumerhandler")



    async def _consumer_handler(self):
        # Guessing that this fails out once the websocket disconnects?
        while True:
            try:
                message = await self.ws.recv()
            except ConnectionClosedError as e:
                # mark us as disconnected before exiting the consumer loop
                # so that the client can know that the connection is gone.
                print(f"Connection closed exception : {sys.exc_info()}")
                logging.error("Exiting read loop WS conection closed")
                await self.disconnect()
                logging.error("_consumer_handler WS disconnected")
                logging.error(e)
                break
            except Exception as e:
                logging.error("_consumer_handler")
                logging.error(e)
                break
            msg_array = json.loads(message)
            for msg in msg_array:
                bp_msg = ButtplugMessage.from_dict(msg)
                logging.debug(bp_msg)
                await self._notify_observers(bp_msg)

    async def send(self, msg: ButtplugMessage):
        msg_str = msg.as_json()
        msg_str = "[" + msg_str + "]"
        logging.debug(msg_str)
        await self.ws.send(msg_str)

    async def disconnect(self):
        await self.ws.close()
        self._connected = False