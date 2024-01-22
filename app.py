# combined_app.py

from flask import Flask, render_template, request, jsonify
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto import Random
from flask_pymongo import PyMongo
from datetime import datetime
import hashlib
import json
import uuid
import base64

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/aircraft_maintenance'
mongo = PyMongo(app)

class AircraftMaintenanceBlockchain:
    def __init__(self):
        self.mongo = mongo
        self.chain = self.load_chain_from_mongo() or []
        self.create_genesis_block()

    def load_chain_from_mongo(self):
        return list(self.mongo.db.blocks.find().sort('index', 1))

    def save_block_to_mongo(self, block):
        self.mongo.db.blocks.insert_one(block)

    def create_genesis_block(self):
        if not self.chain:
            genesis_block = {
                'index': 1,
                'timestamp': str(datetime.now()),
                'aircraft_name': 'Genesis Aircraft',
                'age': 0,
                'changed_components': [],
                'component_repair_history': [],
                'accidental_records': [],
                'previous_hash': '0',
                'nonce': 0
            }
            genesis_block['hash'] = self.hash_block(genesis_block)
            self.save_block_to_mongo(genesis_block)

    def add_block(self, block_data):
        previous_block = self.chain[-1] if self.chain else None
        new_block = {
            'index': previous_block['index'] + 1 if previous_block else 1,
            'timestamp': str(datetime.now()),
            'aircraft_name': block_data['aircraft_name'],
            'age': block_data['age'],
            'changed_components': block_data['changed_components'],
            'component_repair_history': block_data['component_repair_history'],
            'accidental_records': block_data['accidental_records'],
            'previous_hash': previous_block['hash'] if previous_block else '0',
            'nonce': 0
        }
        self.proof_of_work(new_block)
        new_block['hash'] = self.hash_block(new_block)
        self.save_block_to_mongo(new_block)

    def proof_of_work(self, block):
        while not self.is_valid_proof(block):
            block['nonce'] += 1

    def is_valid_proof(self, block):
        block_hash = self.hash_block(block)
        return block_hash[:4] == '0000'  # Adjust difficulty as needed

    def hash_block(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class DigitalSignature:
    def __init__(self):
        self.private_key = RSA.generate(2048, Random.new().read)
        self.public_key = self.private_key.publickey()

    def sign_data(self, data):
        hashed_data = SHA256.new(data.encode())
        signature = pkcs1_15.new(self.private_key).sign(hashed_data)
        return signature

    def verify_signature(self, data, signature, public_key):
        hashed_data = SHA256.new(data.encode())
        try:
            pkcs1_15.new(public_key).verify(hashed_data, signature)
            return True
        except (ValueError, TypeError):
            return False

blockchain = AircraftMaintenanceBlockchain()
digital_signature = DigitalSignature()

@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/add_maintenance', methods=['POST'])
def add_maintenance():
    print(request.form)
    aircraft_name = request.form.get('aircraftName')
    age = int(request.form.get('age', 0))
    changed_components = request.form.get('changedComponents').split(',')
    component_repair_history = request.form.get('componentRepairHistory').split(',')
    accidental_records = request.form.get('accidentalRecords').split(',')

    block_data = {
        'aircraft_name': aircraft_name,
        'age': age,
        'changed_components': changed_components,
        'component_repair_history': component_repair_history,
        'accidental_records': accidental_records
    }

    if not all(block_data.values()):
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

    try:
        # Sign the data
        signature = digital_signature.sign_data(str(block_data))

        # Convert the bytes signature to Base64
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        # Get the previous hash
        previous_hash = blockchain.chain[-1]['hash'] if blockchain.chain else '0'

        # Add the block to the blockchain
        blockchain.add_block(block_data)

        return jsonify({
            'status': 'success',
            'block_data': block_data,
            'signature': signature_base64,
            'previous_hash': previous_hash
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_blocks')
def get_blocks():
    blocks = list(mongo.db.blocks.find({}, {'_id': 0}).sort('index', 1))  # Exclude _id field from the result
    return jsonify({'blocks': blocks})

if __name__ == '__main__':
    app.run(debug=True,port=5200)
