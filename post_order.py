import time
import math
import hashlib
import hmac
import uuid
import sys
import ssl
import certifi
import json
import urllib.request
import base64
from urllib.parse import urlencode


# Post a limit order in bitcoin
class PostOrder:
    ENDPOINT = 'https://api.bitfinex.com/'
    SYMBOL   = 'tBTCUSD'

    def __init__(self, apikeyfile):
        with open(apikeyfile, 'r') as apikeyfile:
            self.apikey = json.load(apikeyfile)

    def post_order(self, price, quantity):

        api_path = 'v2/auth/w/order/submit'
        
        api_key = self.apikey['key']
        api_secret = self.apikey['secret'].encode('utf-8')
        
        timestamp = str(math.floor(time.time() * 1000000.0))
        nonce = timestamp
        order_payload = {
            'type': 'EXCHANGE LIMIT',
            'symbol': self.SYMBOL,
            'price': str(price),
            'amount': str(quantity)
        }

        form_payload = urlencode(order_payload)
        print(form_payload)

        signature_block = '/api/' + api_path + nonce + form_payload
        print(signature_block)


        signature = hmac.new(api_secret,
                             msg=signature_block.encode('utf-8'),
                             digestmod=hashlib.sha384).hexdigest()

        headers = {
            'bfx-nonce': nonce,
            'bfx-apikey': api_key,
            'bfx-signature': signature
        }

        print(headers)

        api_url = self.ENDPOINT + api_path

        api_request = urllib.request.Request(
            api_url,
            headers=headers,
            data=form_payload.encode('utf-8'),
            method='POST'
        )

        with urllib.request.urlopen(api_request, context=ssl.create_default_context(cafile=certifi.where())) as api_call:
            status_code = api_call.getcode()
            api_result = api_call.read()
            headers = api_call.info()                        

            if not status_code == 200:
                print(r)
                print(api_result)
                raise Exception('Status code not 200')

            print(api_result.decode())


if __name__ == '__main__':
    if len(sys.argv) > 2:
        try:
            apikeyfile = sys.argv[1]
            price = sys.argv[2]
            po = PostOrder(apikeyfile)
            po.post_order(float(price), 0.005)
            sys.exit(0)
        except Exception as e:
            print('Failed. '+repr(e))
            print(e.read())
            sys.exit(1)
    else:
        print('apikey file and price are required')
        sys.exit(1)
