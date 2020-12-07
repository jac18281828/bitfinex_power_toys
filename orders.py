`#!/usr/bin/env python

# bitfinex https://docs.bitfinex.com/reference#ws-public-books orders

import certifi
import math
import ssl
import asyncio
import websockets
import traceback
import json
import time
import hmac
import hashlib

class wsclient:

    uri = 'wss://api-pub.bitfinex.com/ws/2'

    def __init__(self, apikeyfile):

        with open(apikeyfile, 'r') as apikeyfile:
            self.apikey = json.load(apikeyfile)
        
        self.update_time = 0.0
        self.sequence = 1
        self.is_running = True


    def increment_sequence(self):
        self.sequence = self.sequence + 1
        return self.sequence

    async def send_json(self, websocket, event):
        event_payload = json.dumps(event)
        print(event_payload)
        await websocket.send(event_payload)        

    async def ping(self, websocket):
        event = {
            'event': 'ping',
            'cid': self.increment_sequence(),
        }
        event_data = json.dumps(event)
        print(event_data)
        await websocket.ping(event_data)

    async def handle_json(self, message, event_dict):
        event = event_dict['event']
        print('event = %s' % event)
        if event == 'auth':
            if event_dict['status'] == 'FAILED':
                self.is_running = False

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


    async def send_auth(self, websocket):

        apikey = self.apikey['key']
        secret = self.apikey['secret']

        # counted millis + a unique index up to 1000
        authnonce = str(math.floor(time.time() * 1000000.0))
        authpayload = 'AUTH' + authnonce
        
        authsig = hmac.new(secret.encode('utf-8'),
                           msg=authpayload.encode('utf-8'),
                           digestmod=hashlib.sha384).hexdigest()

        event = {
            'event': 'auth',
            'apiKey': apikey,
            'authSig': authsig,
            'authPayload': authpayload,
            'authNonce': authnonce,
            'calc': '1',
            'dms': 4,
            'filter': ['trading', 'notify']
        }

        await self.send_json(websocket, event)
        
            
    async def on_open(self, websocket):
        await self.send_auth(websocket)
        
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
    if len(sys.argv) > 1:    
        try:
            apikeyfile = sys.argv[1]
            wsc = wsclient(apikeyfile)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(wsc.run_event_loop())
        except Exception as e:
            print('Not started: %s' % e)
            sys.exit(1)
        finally:
            wsc.is_running = False
            loop.close()
            sys.exit(0)
    else:
        print('apikeyfile is required')
        sys.exit(1)
