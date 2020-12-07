import time
import hashlib
import hmac
import uuid
import sys
import ssl
import certifi
import json
import urllib.request
from urllib.parse import urlencode


# Post a limit order in bitcoin
class PostCancel:
    ENDPOINT = 'https://api.bitfinex.com/'
    SYMBOL   = 'tBTCUSD'

    def __init__(self, apikeyfile):
        with open(apikeyfile, 'r') as apikeyfile:
            self.apikey = json.load(apikeyfile)

    def post_cancel(self, orderid):

        api_path = 'v2/auth/w/order/cancel'
        
        api_key = self.apikey['key']
        api_secret = self.apikey['secret'].encode('utf-8')

        ts = time.gmtime()
        cid_date = time.strftime("%Y-%m-%d", ts)
        print(cid_date)

        cancel_payload = {
            'id': orderid,
            'cid_date': cid_date 
        }

        form_payload = json.dumps(cancel_payload)

        timestamp = str(int(round(time.time() * 1000000.0)))
        nonce = timestamp

        signature_block = '/api/' + api_path + nonce + form_payload

        signature = hmac.new(api_secret,
                             msg=signature_block.encode('utf-8'),
                             digestmod=hashlib.sha384).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'bfx-nonce'

: nonce,
            'bfx-apikey': api_key,
            'bfx-signature': signature
        }

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
            orderid = int(sys.argv[2])
            po = PostCancel(apikeyfile)
            po.post_cancel(orderid)
            sys.exit(0)
        except Exception as e:
            print('Failed. '+repr(e))
            print(e.read())            
            sys.exit(1)
    else:
        print('apikey file and order id are required')
        sys.exit(1)

