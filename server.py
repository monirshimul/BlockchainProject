from flask import Flask, jsonify, request
from blockchain import Blockchain
from node import Nodes
from urllib.parse import urlparse
import requests
#import json

# initialization of all the required object

# creating a blockchain object for using as blockchain database
block_chain = Blockchain()

# getting nodes objects for all adjacent nodes of this node
nodes = Nodes()

# creating a flask app
app = Flask(__name__)
# preventing jsonify of flask from sorting json keys
app.config['JSON_SORT_KEYS'] = False

#
# required functions
#

# sync blockchian when server initialize
def sync_chain():
    all_nodes = nodes.get_nodes()
    for node in all_nodes:
        try:
            fetch_blockchain(node["address"])
        except Exception:
            continue

# for converting a list of block objectid(MongoDB) into string
def senitize_chain(chain):
    for d in chain:
        d["_id"] = str(d["_id"])

def get_formatted_block(block):
    formatted_block = {
        "_id" : str(block["_id"]),
        "index" : block["index"],
        "nonse" : block["nonse"],
        "timestamp" : block["timestamp"],
        "transactions" : block["transactions"],
        "previous_hash" : block["previous_hash"],
        "hash" : block["hash"]
    }
    #print("Formatted block..................")
    #print(formatted_block)
    return formatted_block

# for fetching blockchain form adjacent node when connect
def fetch_blockchain(address):
    try:
        print("Fetching data......")
        response = requests.get(f"http://{address}/get_chain")
        if response.status_code == 200:
            print("get the response")
            json_data = response.json()
            chain = json_data["chain"]
            if len(chain) > block_chain.blockchain.count():
                is_valid = block_chain.is_chain_valid(chain)
                print(chain)
                print("validity : " ,is_valid)
                if is_valid == True:
                    print("replacing chain.....")
                    block_chain.replace_chain(chain)
    except Exception:
        print("fetching failed............")
        raise Exception("Fetching error")

# for circulating new mined of received block to every adjacent block
def circulate_block(block):
    try:
        nds = nodes.get_nodes()
        for node in nds:
            address = node["address"]
            url = f"http://{address}/put_block"
            res = requests.post(url, json=block)
            print(res.text)
    except Exception:
        print("Block can not be circulated to all nodes")
        raise Exception("circulation error")



# for mining a new block
def mine_block():
    try:
        previous_block = block_chain.get_previous_block()
        previous_hash = previous_block["hash"]
        new_block = block_chain.create_block(previous_hash)
        if new_block is None:
            return False
        else:
            formatted_block = get_formatted_block(new_block)
            circulate_block(formatted_block)
            block_chain.transaction_queue.clear()
            return True
    except Exception as ex:
        if str(ex) == "circulation error":
            block_chain.transaction_queue.clear()
            raise ex
        raise Exception("mining error")
        


# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    try:
        chain_list = list(block_chain.blockchain.find())
        senitize_chain(chain_list)
        response = {'chain': chain_list,
                    'length': block_chain.blockchain.count()}
        return jsonify(response) , 200
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Web server or database server down"}), 408

# checking the existing chain validity
@app.route('/is_chain_valid', methods=['GET'])
def is_chain_valid():
    try: 
        chain_status = block_chain.is_chain_valid(list(block_chain.blockchain.find()))
        if chain_status:
            return jsonify({"status" : "Valid"}) , 200
        else:
            return jsonify({"status" : "Invalid"}) , 200
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Web server or database server down"}), 408


# adding new tx and mining the block
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.get_json()
        sender = data["sender"]
        receiver = data["receiver"]
        amount = float(data["amount"])
        _ , is_tx_valid = block_chain.add_transaction(sender=sender, receiver=receiver, amount=amount)
        if is_tx_valid:
            if len(block_chain.transaction_queue) > 2:
                mine_block()
                return jsonify({"status" : "your transaction is added in blockchain", "block_number" : block_chain.blockchain.count()}) , 200
            return jsonify({"status" : "your transaction will be added", "block_number" : block_chain.blockchain.count() + 1}) , 200
        else:
            return jsonify({"status" : "invalid transaction"}) , 200
    except Exception as ex:
        return jsonify({"status" : "Exception occured", "message" : f"Request can not be parsed or {str(ex)}"}), 500

@app.route('/calculate_balance', methods=['POST'])
def calculate_balance():
    try:
        data = request.get_json()
        name = data["name"]
        balance = block_chain.calculate_balance(list(block_chain.blockchain.find()),name)
        return jsonify({"balance" : balance , "name" : name}), 200
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Request can not be parsed or database server down"}), 500



#
# receiving new circulated block
#

@app.route('/put_block', methods=['POST'])
def put_block():
    try:
        block = request.get_json()
        previous_block = block_chain.get_previous_block()
        if previous_block["index"] + 1 == block["index"] and previous_block["hash"] == block["previous_hash"] and block["hash"][:4] == "0000":
            block_chain.blockchain.insert(block)
            return jsonify({"status" : "true"}) , 200
        else:
            return jsonify({"status" : "false"}) , 200
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Request can not be parsed or database server down"}), 500


#
# node management- insert, delete, show
#
@app.route('/add_node', methods = ['POST'])
def add_node():
    try:
        data = request.get_json()
        name = data['name']
        address = data['address']
        parsed_address = urlparse(address)
        nodes.add_node(name, parsed_address.netloc)
        fetch_blockchain(parsed_address.netloc)
        return jsonify({"status": "success"}), 201
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Server down or blockchain can not be fetched from added node"}), 500

@app.route('/delete_node', methods = ['POST'])
def delete_node():
    try:
        data = request.get_json()
        name = data["name"]
        nodes.delete_node(name)
        return jsonify({"status": "success"}), 200
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Server down"}), 500

@app.route('/show_nodes', methods = ['GET'])
def show_nodes():
    try:
        lnodes = nodes.get_nodes()
        senitize_chain(lnodes)
        return jsonify(lnodes), 200
    except Exception:
        return jsonify({"status" : "Exception occured", "message" : "Server down or sanitization error"}), 500

# sync the blockchian
try:
    sync_chain()
except Exception as ex:
    print(str(ex))

# Running the app
app.run(host = '0.0.0.0', port = 5000)