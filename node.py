from pymongo import MongoClient

class Nodes :

    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017')
        self.db = self.client.mydb
        self.nodes = self.db.nodes

    def get_nodes(self):
        return list(self.nodes.find())

    def add_node(self, name, address):
        node = {
            "name" : name,
            "address" : address
        }
        self.nodes.insert(node)
        return node

    def delete_node(self, name):
        self.nodes.delete_one({
            "name" : name
        })

