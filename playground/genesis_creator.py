import hashlib
import json


genesis = {
    "index" : 1,
    "nonse" : 1,
    "timestamp" : "2018-09-12 11:18:16.230905",
    "transactions" : [],
    "previous_hash" : "0"
} 

#print(str(genesis))

def hash(g):
    encoded_block = json.dumps(str(g), sort_keys = True).encode()
    return hashlib.sha256(encoded_block).hexdigest()

valid_hash = hash(genesis)

while valid_hash[:4] != "0000":
    genesis["nonse"] += 1
    #print("first hash: ", valid_hash)
    valid_hash = hash(genesis)
print(valid_hash)
print(genesis)
