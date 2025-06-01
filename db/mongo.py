from pymongo import MongoClient

def get_mongo_client():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        return client["socialscopemongo"]
    except Exception as e:
        print("MongoDB connection error:", e)
        return None
