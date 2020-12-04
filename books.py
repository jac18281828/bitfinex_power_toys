#!/usr/bin/env python

import certifi
import ssl
import asyncio
import websockets
import traceback
import json
import time
import zlib
import datetime
from decimal import Decimal

# Example implementation including the bitfinex checksum

class wsclient:

    SYMBOL = 'tETHUSD' #'tBTCUSD'

    URI = 'wss://api-pub.bitfinex.com/ws/2'

    def __init__(self):
        self.update_time = 0.0
        self.last_sequence = 1
        self.sequence = 1
        self.is_running = True

        self.bids = {}
        self.asks = {}

    async def send_json(self, websocket, event):
        event_payload = json.dumps(event)
        print(event_payload)
        await websocket.send(event_payload)        

    async def ping(self, websocket):
        await websocket.ping()

    async def handle_json(self, message, event_dict):
        print('event = %s' % event_dict['event'])

    def format_entry(self, orderid, amount):

        entry = '{:d}'.format(orderid) + ':'
        ## 8 here, expected digits for floating point precision
        return entry + '{0:.8f}'.format(amount).rstrip('0').rstrip('.')
            

    async def handle_checksum(self, checksum):
        print("checksum = %d" % checksum)

        # by price then orderid, orderid always ascending
        
        bids = sorted(self.bids.values(), key=lambda entry: (entry[1], -entry[0]), reverse=True)
        asks = sorted(self.asks.values(), key=lambda entry: (entry[1], entry[0]))

        print(json.dumps(bids[0:3]))
        print(json.dumps(asks[0:3]))

        # of orderid:amount
        crclist = []
        for i in range(0, 25):
            if len(bids) > i:
                b = bids[i]
                crclist.append(self.format_entry(b[0], b[2]))
            if len(asks) > i:
                a = asks[i]
                crclist.append(self.format_entry(a[0], a[2]))

        csstr = ':'.join(crclist)
        
        crc32 = zlib.crc32(csstr.encode('utf-8'))

        cs_unsigned = checksum & 0xffffffff
        if crc32 != cs_unsigned:
            print ("Checksum failure: %d != %d" %(crc32, cs_unsigned))
            print('cs str = %s' % csstr)
            print (datetime.datetime.now())
            self.is_running = False

    async def handle_update(self, level):
        if(len(level) > 0):
            orderid=level[0]
            price=level[1]
            amount=level[2]

            if price == 0:
                if orderid in self.bids:
                    del self.bids[orderid]
                if orderid in self.asks:
                    del self.asks[orderid]
            else:
                if amount > 0:
                    self.bids[orderid] = level
                else:
                    if amount < 0:
                        self.asks[orderid] = level

            print("%d:%g:%g" % (orderid, price, amount))

    async def handle_snapshot(self, event_list):
        for event in event_list:
            await self.handle_update(event)

    async def handle_model(self, message, event_dict):
        print('channel %d' % event_dict[0])

        if isinstance(event_dict[1], str):
            event_type = event_dict[1]
            print('event   %s' % event_type)
            if event_type == 'cs':
                await self.handle_checksum(event_dict[2])
        else:
            payload = event_dict[1]
            print('payload %s' % payload)

            if(len(payload) > 0):
                element = payload[0]
                if isinstance(element, list):
                    await self.handle_snapshot(payload)
                else:
                    await self.handle_update(payload)


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
            #await self.ping(websocket)
        else:
            await asyncio.sleep(1 - timedelta)


    async def send_subscription(self, websocket):
        event = {
            'event': 'subscribe',
            'channel': 'book',
	    'freq': 'F0',
	    'prec': 'R0',
            'symbol': self.SYMBOL,
        }


        await self.send_json(websocket, event)

        event = {
            'event': 'subscribe',
            'channel': 'status',
            'key': self.SYMBOL,
        }

        await self.send_json(websocket, event)

        event = {
            'event': 'conf',
            'flags': 0x20000,
        }

        await self.send_json(websocket, event)
        
            
            
    async def on_open(self, websocket):
        await self.send_subscription(websocket)
        
    async def run_event_loop(self):
        try:
            async with websockets.connect(self.URI, ssl=ssl.create_default_context(cafile=certifi.where())) as websocket:

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
