import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv() 

client = MongoClient(os.environ["MONGODB_URI"])
db = client["dispatch"]          # 👈 choose a DB name
incidents = db["calls"]  

with open("data.json") as f:
    calls = json.load(f)

for c in calls:
    c["createdAt"] = datetime.utcnow()
    c["updatedAt"] = datetime.utcnow()

incidents.insert_many(calls)
print("Seeded incidents")
