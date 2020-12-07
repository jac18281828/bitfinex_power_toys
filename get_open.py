import time
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

    def post_order(self):

        api_path = 'v2/auth/r/orders'
        
        api_key = self.apikey['key']
        
        api_secret = self.apikey['secret'].encode('utf-8')

        
        timestamp = str(int(round(time.time() * 1000000.0)))
        nonce = timestamp

        order_payload = {}

        body = urlencode(order_payload)

        signature_block = '/api/' + api_path + nonce + body

        signature = hmac.new(api_secret, msg=signature_block.encode('utf-8'), digestmod=hashlib.sha384).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'bfx-nonce': nonce,
            'bfx-apikey': api_key,
            'bfx-signature': signature
        }

        api_url = self.ENDPOINT + api_path

        print(api_url)

        api_request = urllib.request.Request(
            api_url,
            headers=headers,
            data=body.encode('utf-8')
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
    if len(sys.argv) > 1:
        try:
            apikeyfile = sys.argv[1]
            po = PostOrder(apikeyfile)
            po.post_order()
            sys.exit(0)
        except Exception as e:
            print('Failed. '+repr(e))
            sys.exit(1)
    else:
        print('apikeyfile is required')
        sys.exit(1)


            
