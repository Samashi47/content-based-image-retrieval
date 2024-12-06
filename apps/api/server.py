from flask import Response, request, Flask
from flask_cors import CORS
import json
import random
import datetime
import hashlib
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import jwt
import os
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Hello World"

@app.route('/auth/login', methods=['POST'])
def login():
    hash_func = hashlib.sha256()
    data = request.json    
    hash_func.update(data['password'].encode())
    hashed_password = hash_func.hexdigest()
    hash_func = hashlib.sha256()
    hash_func.update('12345678'.encode())
    test_hashed_password = hash_func.hexdigest()

    if data['email'] == 'test@test.com' and hashed_password == test_hashed_password:
        private_key = open('.ssh/jwt-key', 'rb').read()
        key = load_pem_private_key(private_key, password=None, backend=default_backend())
        payload = {
            'email': 'test@test.com',
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        }
        token = jwt.encode(payload, key, algorithm='RS256')
        
        return Response(json.dumps({'token': token}), mimetype='application/json', status=200)
    else:
        return Response(json.dumps({'message': 'Login Failed'}), mimetype='application/json', status=401) 
    

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')