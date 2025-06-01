SocialScope
===========

SocialScope is a web application for analyzing and visualizing social network data using two NoSQL databases: MongoDB and Neo4j.  
The app is built with Flask, and is based on the LDBC Social Network Benchmark (SNB) dataset.

 Features
-----------

**Lookup Queries**
- User Activity Timeline (MongoDB only): View a chronological list of a person’s posts and comments.
- Professional Network Explorer (Neo4j only): Find co-workers or classmates linked to the same organisation.
- Forum Explorer (MongoDB + Neo4j): List forums joined by a person, with forum and moderator details.

**Analytical Queries**
- Influencer Radar (Neo4j only): Top 10 people with the most KNOWS relationships.
- Like Leaderboard (MongoDB + Neo4j): Top 10 most liked posts and comments, enriched with user info.

 Tech Stack
-------------

- Backend: Python 3, Flask
- Databases:
  - MongoDB (document store)
  - Neo4j (graph database)
- Frontend: HTML, Jinja2, Chart.js

Dataset Preparation
----------------------

**LDBC SNB Dataset**
- Generated using Docker from the official Spark generator:
  docker build -t ldbc_spark_gen .
  docker run --rm -v C:\Users\houba\Desktop\social_network_2:/out ldbc_spark_gen -- --scale-factor 0.1 --output-dir /out --format csv --mode bi

**MongoDB Import**
- CSVs were cleaned with a Python script (clean_and_import.py)
- Script parses dates and converts number types automatically
- Imported collections: persons, posts, comments, forums, tags, tagclasses

**Neo4j Import**
- Used LOAD CSV WITH HEADERS and FIELDTERMINATOR '|'
- Only essential properties and nodes imported
- Nodes: Person, Tag, Forum, Organisation, Comment, Post, TagClass  
- Relationships: HAS_INTEREST, KNOWS, MEMBER_OF, WORKS_AT, HAS_TAG, LIKES

 How to Run Locally
----------------------

1. Clone the repository:
   git clone https://github.com/iheb-hidouri-28/socialscope.git
   cd socialscope

2. Create and activate virtual environment:
   python -m venv venv
   venv\Scripts\activate  (on Windows)

3. Install dependencies:
   pip install -r requirements.txt

4. Start MongoDB and Neo4j locally

5. Run the app:
   python app.py

Then visit http://localhost:5050 in your browser.


Folder Structure
-------------------
├── app.py  
├── clean_and_import.py  
├── db/  
│   ├── mongo.py  
│   └── neo4j.py  
├── templates/  
│   ├── base.html  
│   ├── home.html  
│   ├── activity_timeline.html  
│   ├── professional_network.html  
│   ├── forum_explorer.html  
│   ├── influencer_radar.html  
│   └── like_leaderboard.html  
├── requirements.txt  
└── README.md  

 Author
-----------
Iheb Hidouri  
Università degli Studi di Torino  
Academic Year 2024–2025

 License
----------
This project is for educational purposes only and part of the MAADB NoSQL Lab Project , università degli studi di  torino .
