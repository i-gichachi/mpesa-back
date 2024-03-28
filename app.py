from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
import requests
import base64
import datetime
import json

app = Flask(__name__)
CORS(app)
api = Api(app)

# M-Pesa Credentials and Constants
CONSUMER_KEY = 'C77Sai2IlV9JCjXqQAvlbv2NN4bKAVVMM6sKyurXmTWzrycS'
CONSUMER_SECRET = 'GyhAqxgQVmi6Km2VrtxawVOqx6DlE8mSyBj590qhaMftCdnia9InxMpbpyLGwG2m'
BUSINESS_SHORT_CODE = '174379'
LIPA_NA_MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'  
CALLBACK_URL = 'https://mpesa-8s4l.onrender.com/stk-callback'

def get_access_token():
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    credentials = base64.b64encode(f'{CONSUMER_KEY}:{CONSUMER_SECRET}'.encode()).decode('utf-8')
    headers = {'Authorization': f'Basic {credentials}'}
    response = requests.get(api_url, headers=headers)
    return response.json().get('access_token')

def stk_push(phone_number, amount=1):
    access_token = get_access_token()
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {'Authorization': f'Bearer {access_token}'}

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{BUSINESS_SHORT_CODE}{LIPA_NA_MPESA_PASSKEY}{timestamp}'.encode()).decode('utf-8')

    payload = {
        'BusinessShortCode': BUSINESS_SHORT_CODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,  
        'PartyA': phone_number,  
        'PartyB': BUSINESS_SHORT_CODE,
        'PhoneNumber': phone_number, 
        'CallBackURL': CALLBACK_URL,
        'AccountReference': 'Donation Y',
        'TransactionDesc': 'Donate'
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

class STKPushResource(Resource):
    def post(self):
        data = request.get_json()
        phone_number = data.get('phone_number')
        amount = data.get('amount')

        if not phone_number or not amount:
            return {'error': 'Missing phone number or amount'}, 400

        response = stk_push(phone_number, amount)
        return response

api.add_resource(STKPushResource, '/stk-push')

class STKCallbackResource(Resource):
    def post(self):
        data = request.get_json()
        if data is None:
            app.logger.error("Callback received empty data")
            return {'error': 'Empty callback data'}, 400

        try:
            app.logger.info(f"Callback Data: {json.dumps(data)}")

            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            mpesa_receipt_number = data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])[1].get('Value')
            
            return {'status': 'success', 'message': 'Callback processed successfully'}
        except Exception as e:
            app.logger.error(f"Error processing callback: {e}")
            return {'error': 'Error processing callback'}, 500

api.add_resource(STKCallbackResource, '/stk-callback')

if __name__ == '__main__':
    app.run(port=5555, debug=True)