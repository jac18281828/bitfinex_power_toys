#!/usr/bin/env python

import certifi
import ssl
import asyncio
import websockets
import traceback
import json
import time

class wsclient:

    uri = 'wss://api-pub.bitfinex.com/ws/2'

    def __init__(self):
        self.update_time = 0.0
        self.last_sequence = 1
        self.sequence = 1
        self.is_running = True

    async def send_json(self, websocket, event):
        event_payload = json.dumps(event)
        print(event_payload)
        await websocket.send(event_payload)        

    async def ping(self, websocket):
        await websocket.ping()

    async def handle_json(self, message, event_dict):
        print('event = %s' % event_dict['event'])

    async def handle_model(self, message, event_dict):
        print('channel %d' % event_dict[0])

        if isinstance(event_dict[1], str):
            print('event   %s' % event_dict[1])
        else:
            print('payload %s' % event_dict[1])


    async def handle_message(self, message, websocket):
        try:
            print(message)
            event_dict = json.loads(message)

            if 'event' in event_dict:
                await self.handle_json(message, event_dict)
            else:
                await self.handle_model(message, event_dict)
        finally:
            self.update_time = time.time()

    async def message_reader(self, websocket):
        async for message in websocket:
            await self.handle_message(message, websocket)

    async def heartbeat(self, websocket):
        now = time.time()
        timedelta = now - self.update_time
        if timedelta >= 1:
            self.update_time = time.time()
            await self.ping(websocket)
        else:
            await asyncio.sleep(1 - timedelta)


    async def send_subscription(self, websocket):

        event = {
            'event': 'subscribe',
            'channel': 'status',
            'key': 'tBTCUSD'
        }

        await self.send_json(websocket, event)
        
            
            
    async def on_open(self, websocket):
        await self.send_subscription(websocket)
        
    async def run_event_loop(self):
        try:
            async with websockets.connect(self.uri, ssl=ssl.create_default_context(cafile=certifi.where())) as websocket:

                await self.on_open(websocket)
                
                while self.is_running:

                    tasks = [
                        asyncio.ensure_future(self.message_reader(websocket)),
                        asyncio.ensure_future(self.heartbeat(websocket))
                    ]
                    
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    
                    for task in pending:
                        task.cancel()
                        
        except Exception as e:
            print('error: %s' % e)
            print(traceback.format_exc(e))


if __name__ == '__main__':
    try:
        wsc = wsclient()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(wsc.run_event_loop())
    finally:
        wsc.is_running = False
        loop.close()
