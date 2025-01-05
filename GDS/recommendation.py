from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Function to setup GDS graph
def setup_gds_graph(session):
    session.run("CALL gds.graph.drop('movieRecommendationGraph', false) YIELD graphName;")
    session.run("""
    CALL gds.graph.project(
        'movieRecommendationGraph',
        ['User', 'Movie'],
        {
            WATCHED: {
                type: 'WATCHED',
                properties: 'rating'
            }
        }
    );
    """)
    print("GDS graph projection created successfully!")

# Function for collaborative filtering recommendations
def get_collaborative_recommendations(user_id, session):
    query = """
    MATCH (u:User {id: $user_id})-[:WATCHED]->(m:Movie)<-[:WATCHED]-(other:User)-[:WATCHED]->(rec:Movie)
    WHERE NOT (u)-[:WATCHED]->(rec)
    RETURN rec.title AS recommendation, COUNT(*) AS score
    ORDER BY score DESC
    LIMIT 5;
    """
    result = session.run(query, user_id=user_id)
    return [record["recommendation"] for record in result]

# Function for content-based recommendations
def get_content_based_recommendations(user_id, session):
    query = """
    MATCH (u:User {id: $user_id})-[:WATCHED]->(m:Movie)
    WITH u, m
    MATCH (rec:Movie)
    WHERE NOT (u)-[:WATCHED]->(rec)
    WITH m, rec,
         apoc.text.jaccardSimilarity(m.genres, rec.genres) AS genre_similarity,
         1.0 / (1.0 + abs(m.release_year - rec.release_year)) AS year_similarity
    RETURN rec.title AS recommendation, MAX(genre_similarity + year_similarity) AS score
    ORDER BY score DESC
    LIMIT 5;
    """
    result = session.run(query, user_id=user_id)
    return [record["recommendation"] for record in result]

# Main function to get recommendations
def get_recommendations(user_id):
    with driver.session() as session:
        # Setup GDS graph
        setup_gds_graph(session)

        # Try collaborative filtering
        print(f"Getting recommendations for User {user_id} using Collaborative Filtering...")
        recommendations = get_collaborative_recommendations(user_id, session)

        # Fallback to content-based filtering if no recommendations
        if not recommendations:
            print(f"No collaborative recommendations found. Falling back to Content-Based Filtering...")
            recommendations = get_content_based_recommendations(user_id, session)

        # Return recommendations
        return recommendations

# Entry point
if __name__ == "__main__":
    try:
        user_id = 1 # Example user ID
        recommendations = get_recommendations(user_id)
        print(f"Recommendations for User {user_id}: {recommendations}")
    finally:
        driver.close()
