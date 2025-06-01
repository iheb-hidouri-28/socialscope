from neo4j import GraphDatabase

def get_neo4j_driver():
    try:
        uri = "bolt://localhost:7687"
        auth = ("neo4j", "ihebazer123")  # ← replace with your real Neo4j password
        driver = GraphDatabase.driver(uri, auth=auth)
        return driver
    except Exception as e:
        print("Neo4j connection error:", e)
        return None
