from flask import Flask, render_template, request
from db.mongo import get_mongo_client
from db.neo4j import get_neo4j_driver
from datetime import datetime

app = Flask(__name__)


# Filter: Format ISO datetime for templates
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except Exception:
            return value
    return value.strftime(format)

# Helper: Check if a person exists
def person_exists(db, person_id):
    return db.persons.find_one({"id": person_id}) is not None


# Static Pages
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/lookup")
def lookup():
    return render_template("lookup.html")


# Lookup: User Activity Timeline (MongoDB)
@app.route("/lookup/activity")
def lookup_activity():
    db = get_mongo_client()
    person_id = request.args.get("person_id", type=int)
    activity, message = [], None

    if person_id:
        if not person_exists(db, person_id):
            message = f"Person ID {person_id} not found."
        else:
            pipeline = [
                {"$match": {"CreatorPersonId": person_id}},
                {"$project": {"id": 1, "creationDate": 1, "type": {"$literal": "post"}, "content": "$content", "imageFile": "$imageFile"}},
                {"$unionWith": {
                    "coll": "comments",
                    "pipeline": [
                        {"$match": {"CreatorPersonId": person_id}},
                        {"$project": {"id": 1, "creationDate": 1, "type": {"$literal": "comment"}, "content": "$content"}}
                    ]
                }},
                {"$sort": {"creationDate": 1}}
            ]
            activity = list(db.posts.aggregate(pipeline))
            if not activity:
                message = f"No posts or comments found for Person ID {person_id}."

    return render_template("activity_timeline.html", activity=activity, person_id=person_id, message=message)


# Lookup: Professional Network (Neo4j)
@app.route("/lookup/network")
def professional_network():
    db = get_mongo_client()
    driver = get_neo4j_driver()
    person_id = request.args.get("person_id", type=int)
    connections, message = [], None

    if person_id:
        if not person_exists(db, person_id):
            message = f"Person ID {person_id} not found."
        else:
            with driver.session() as session:
                result = session.run("""
                    MATCH (me:Person {id: $person_id})-[:WORKS_AT|STUDY_AT]->(org:Organisation)<-[:WORKS_AT|STUDY_AT]-(other:Person)
                    WHERE me <> other
                    RETURN DISTINCT other.id AS personId,
                                    other.firstName + ' ' + other.lastName AS fullName,
                                    org.name AS organisationName,
                                    org.type AS organisationType
                    ORDER BY organisationName
                """, person_id=person_id)
                connections = [dict(r) for r in result]
            if not connections:
                message = f"No coworkers/classmates found for Person ID {person_id}."

    return render_template("professional_network.html", connections=connections, person_id=person_id, message=message)


# Lookup: Forum Explorer (Cross-database)
@app.route("/lookup/forums")
def forum_explorer():
    db = get_mongo_client()
    driver = get_neo4j_driver()
    person_id = request.args.get("person_id", type=int)
    forums, message = [], None

    if person_id:
        if not person_exists(db, person_id):
            message = f"Person ID {person_id} not found."
        else:
            with driver.session() as session:
                result = session.run("""
                    MATCH (p:Person {id: $person_id})-[:MEMBER_OF]->(f:Forum)
                    RETURN DISTINCT f.id AS forum_id
                """, person_id=person_id)
                forum_ids = [r["forum_id"] for r in result]

            if forum_ids:
                pipeline = [
                    {"$match": {"id": {"$in": forum_ids}}},
                    {"$lookup": {
                        "from": "persons",
                        "localField": "ModeratorPersonId",
                        "foreignField": "id",
                        "as": "moderator"
                    }},
                    {"$unwind": "$moderator"},
                    {"$project": {
                        "id": 1,
                        "title": 1,
                        "creationDate": 1,
                        "moderatorName": {"$concat": ["$moderator.firstName", " ", "$moderator.lastName"]}
                    }}
                ]
                forums = list(db.forums.aggregate(pipeline))
            else:
                message = f"No forums found for Person ID {person_id}."

    return render_template("forum_explorer.html", forums=forums, person_id=person_id, message=message)


# Analytical: Influencer Radar (Neo4j)
@app.route("/analytics/influencers")
def influencer_radar():
    driver = get_neo4j_driver()
    influencers, message = [], None

    with driver.session() as session:
        result = session.run("""
            MATCH (p:Person)-[:KNOWS]->(friend)
            RETURN p.id AS personId,
                   p.firstName + ' ' + p.lastName AS fullName,
                   COUNT(friend) AS friendCount
            ORDER BY friendCount DESC
            LIMIT 10
        """)
        influencers = [dict(r) for r in result]

    if not influencers:
        message = "No influencer data found."

    return render_template("influencer_radar.html", influencers=influencers, message=message)


# Analytical: Like Leaderboard (Cross-database)
@app.route("/analytics/likes")
def like_leaderboard():
    db = get_mongo_client()
    driver = get_neo4j_driver()

    with driver.session() as session:
        post_likes = list(session.run("""
            MATCH (:Person)-[r:LIKES]->(p:Post)
            RETURN p.id AS postId, COUNT(r) AS likeCount
            ORDER BY likeCount DESC LIMIT 10
        """))

        comment_likes = list(session.run("""
            MATCH (:Person)-[r:LIKES]->(c:Comment)
            RETURN c.id AS commentId, COUNT(r) AS likeCount
            ORDER BY likeCount DESC LIMIT 10
        """))

    post_ids = [r["postId"] for r in post_likes]
    comment_ids = [r["commentId"] for r in comment_likes]

    post_results = list(db.posts.aggregate([
        {"$match": {"id": {"$in": post_ids}}},
        {"$lookup": {
            "from": "persons",
            "localField": "CreatorPersonId",
            "foreignField": "id",
            "as": "creator"
        }},
        {"$unwind": "$creator"},
        {"$project": {
            "id": 1,
            "content": 1,
            "imageFile": 1,
            "creationDate": 1,
            "creatorName": {"$concat": ["$creator.firstName", " ", "$creator.lastName"]}
        }}
    ]))

    comment_results = list(db.comments.aggregate([
        {"$match": {"id": {"$in": comment_ids}}},
        {"$lookup": {
            "from": "persons",
            "localField": "CreatorPersonId",
            "foreignField": "id",
            "as": "creator"
        }},
        {"$unwind": "$creator"},
        {"$project": {
            "id": 1,
            "content": 1,
            "creationDate": 1,
            "creatorName": {"$concat": ["$creator.firstName", " ", "$creator.lastName"]}
        }}
    ]))

    post_map = {doc["id"]: doc for doc in post_results}
    comment_map = {doc["id"]: doc for doc in comment_results}

    topLikedPosts = [{
        "id": r["postId"],
        "likes": r["likeCount"],
        "content": post_map[r["postId"]].get("content"),
        "imageFile": post_map[r["postId"]].get("imageFile"),
        "creatorName": post_map[r["postId"]].get("creatorName"),
        "created": post_map[r["postId"]].get("creationDate")
    } for r in post_likes if r["postId"] in post_map]

    topLikedComments = [{
        "id": r["commentId"],
        "likes": r["likeCount"],
        "content": comment_map[r["commentId"]].get("content"),
        "creatorName": comment_map[r["commentId"]].get("creatorName"),
        "created": comment_map[r["commentId"]].get("creationDate")
    } for r in comment_likes if r["commentId"] in comment_map]

    return render_template("like_leaderboard.html", topLikedPosts=topLikedPosts, topLikedComments=topLikedComments)

# --------------------------
# Run app
# --------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5050)
