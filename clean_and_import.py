import csv
import os
from pymongo import MongoClient
from dateutil.parser import parse as date_parse

# Adjust this path to your cleaned LDBC dataset
DATASET_DIR = r"C:\Users\houba\Desktop\EXAMS\MAABDs\Dataset\clean_mongo"

client = MongoClient("mongodb://localhost:27017/")
db = client["socialscopemongo"]

files_to_collections = {
    "Person.csv": "persons",
    "Post.csv": "posts",
    "Comment.csv": "comments",
    "Forum.csv": "forums",
    "Tag.csv": "tags",
    "TagClass.csv": "tagclasses"
}

def try_convert(value):
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        pass
    try:
        # Detect ISO date strings (e.g. 2011-07-28T08:59:04.909+00:00)
        if "T" in value and "+" in value:
            return date_parse(value)
    except Exception:
        pass
    return value  # fallback to string

def clean_and_insert(file_name, collection_name):
    path = os.path.join(DATASET_DIR, file_name)
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        headers = next(reader)
        documents = []
        for row in reader:
            doc = {headers[i]: try_convert(row[i]) for i in range(len(headers))}
            documents.append(doc)
        print(f"Inserting {len(documents)} documents into '{collection_name}'")
        db[collection_name].drop()
        db[collection_name].insert_many(documents)

if __name__ == "__main__":
    for file, collection in files_to_collections.items():
        clean_and_insert(file, collection)
    print("✅ All collections imported with type conversion and datetime parsing.")
