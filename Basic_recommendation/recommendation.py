from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

class MovieRecommendationSystem:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def content_based_recommendation(self, user_name):
        query = """
        MATCH (u:User {name: $user_name})-[:WATCHED]->(m:Movie)-[:BELONGS_TO]->(g:Genre)<-[:BELONGS_TO]-(rec:Movie)
        WHERE NOT (u)-[:WATCHED]->(rec)
        RETURN DISTINCT rec.title AS recommendation, rec.genre AS genre, rec.release_year AS year, rec.rating AS rating
        ORDER BY rec.rating DESC
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, user_name=user_name)
            return [record for record in result]

    def collaborative_filtering_recommendation(self, user_name):
        query = """
        MATCH (u1:User {name: $user_name})-[:WATCHED]->(m:Movie)<-[:WATCHED]-(u2:User)-[:WATCHED]->(rec:Movie)
        WHERE NOT (u1)-[:WATCHED]->(rec)
        RETURN DISTINCT rec.title AS recommendation, rec.genre AS genre, rec.release_year AS year, rec.rating AS rating
        ORDER BY rec.rating DESC
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, user_name=user_name)
            return [record for record in result]

# Instantiate the system
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)
neo4j_uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

recommender = MovieRecommendationSystem(neo4j_uri, username, password)

# Content-Based Recommendation
print("Content-Based Recommendations for Alice:")
recommendations = recommender.content_based_recommendation("Alice")
for rec in recommendations:
    print(f"Movie: {rec['recommendation']}, Genre: {rec['genre']}, Year: {rec['year']}, Rating: {rec['rating']}")

# Collaborative Filtering Recommendation
print("\nCollaborative Filtering Recommendations for Alice:")
recommendations = recommender.collaborative_filtering_recommendation("Alice")
for rec in recommendations:
    print(f"Movie: {rec['recommendation']}, Genre: {rec['genre']}, Year: {rec['year']}, Rating: {rec['rating']}")

recommender.close()
