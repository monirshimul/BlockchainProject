import datetime
import hashlib
import json
#from flask import Flask, jsonify
from pymongo import MongoClient

class Blockchain :

    def __init__(self) :
        self.client = MongoClient('mongodb://localhost:27017')
        self.db = self.client.mydb
        self.blockchain = self.db.blockchain
        self.transaction_queue = []

    
    # for getting the last block of blockchain
    def get_previous_block(self):
        last_block_cursor = self.blockchain.find().skip(self.blockchain.count() - 1)
        for last_block in last_block_cursor :
            return last_block

    # for adding valid transactions in the mempool which is transaction_queue
    def add_transaction(self, sender, receiver, amount):
        if sender == "CENTRAL BANK" :
            self.transaction_queue.append({
                "sender" : sender,
                "receiver" : receiver,
                "amount" : amount
            })
            return self.get_previous_block()["index"] + 1, True
        else:
            chain_list = list(self.blockchain.find())
            balance = self.calculate_balance(chain_list, sender)
            if balance >= amount and amount > 0:
                self.transaction_queue.append({
                    "sender" : sender,
                    "receiver" : receiver,
                    "amount" : amount
                })
                return self.get_previous_block()["index"] + 1, True
        return "Invalid Transaction", False

    # for claculating the balance of a sender from blockchain
    def calculate_balance(self, chain_list, sender):
        balance = 0
        for block in chain_list:
            if len(block["transactions"]) > 0:
                for tx in block["transactions"]:
                    if tx["receiver"] == sender :
                        balance += tx["amount"]
                    elif tx["sender"] == sender:
                        balance -= tx["amount"]
        return balance
    
    # for hashing a block
    def hasher(self, g):
        encoded_block = json.dumps(g, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    # for mining a block with proof-of-work
    def create_block(self, previous_hash):
        block_data = {
            "index" : self.blockchain.count() + 1,
            "nonse" : 1,
            "timestamp" : str(datetime.datetime.now()),
            "transactions" : self.transaction_queue,
            "previous_hash" : previous_hash,
        }
        # finding the proof-of-work
        valid_hash = self.hasher(str(block_data))
        while valid_hash[:4] != "0000":
            block_data["nonse"] += 1
            valid_hash = self.hasher(str(block_data))
        
        # creating block for block chain
        block = {
            "index" : block_data["index"],
            "nonse" : block_data["nonse"],
            "timestamp" : block_data["timestamp"],
            "transactions" : block_data["transactions"],
            "previous_hash" : block_data["previous_hash"],
            "hash" : valid_hash
        }
        self.blockchain.insert(block)
        #self.transaction_queue.clear()
        return block

    # for checking the validity of the blockchain
    def is_chain_valid(self, chain_list):

        previous_block = chain_list[0]
        for index in range(1,len(chain_list)):
            block = chain_list[index]
            if previous_block["hash"] != block["previous_hash"]:
                print("link is broken.....")
                return False
            hashable_block = {
                 "index" : block["index"],
                 "nonse" : block["nonse"],
                 "timestamp" : block["timestamp"],
                "transactions" : block["transactions"],
                "previous_hash" : block["previous_hash"],
            }
            block_current_hash = self.hasher(str(hashable_block))
            print("current hash: ", block_current_hash)
            print("block stored hash: ", block["hash"])
            if block_current_hash != block["hash"] or block_current_hash[:4] != "0000":
                print("block is tempered or proof of work error")
                return False     
            previous_block = block

        return True

    # for replacing with longest chain
    def replace_chain(self, chain):
        self.blockchain.delete_many({})
        for block in chain:
            self.blockchain.insert(block)
    

