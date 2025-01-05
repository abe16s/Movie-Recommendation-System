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

# Function to create similarity relationships using GDS
def create_similarity_relationships(session):
    # Using GDS nodeSimilarity for content-based filtering
    session.run("""
    MATCH (m1:Movie), (m2:Movie)
    WHERE m1 <> m2 // Ensure each pair is processed only once
    WITH m1, m2,
        [genre IN m1.genres WHERE genre IN m2.genres] AS common_genres,
        m1.genres + [genre IN m2.genres WHERE NOT genre IN m1.genres] AS all_genres,
        1.0 / (1.0 + abs(m1.release_year - m2.release_year)) AS year_similarity
    WHERE size(all_genres) > 0 // Avoid division by zero
    WITH m1, m2, 
        size(common_genres) * 1.0 / size(all_genres) AS genre_similarity, 
        year_similarity
    WHERE genre_similarity > 0.1 // Adjust threshold as needed
    MERGE (m1)-[:SIMILAR {similarity: genre_similarity + year_similarity}]->(m2)
    """)
    print("Similarity relationships created using GDS!")

    # Using GDS performs worse creates small relations and similarities
    # CALL gds.nodeSimilarity.stream('movieRecommendationGraph')
    # YIELD node1, node2, similarity
    # WITH gds.util.asNode(node1) AS movie1, gds.util.asNode(node2) AS movie2, similarity
    # WHERE similarity > 0.5  // Only highly similar movies
    # MERGE (movie1)-[r:SIMILAR]->(movie2)
    # SET r.similarity = similarity; 

# Function for collaborative filtering recommendations using GDS
def get_collaborative_recommendations(user_id, session):
    query = """
    MATCH (u:User {id: $user_id})
    CALL gds.nodeSimilarity.stream('movieRecommendationGraph')
    YIELD node1, node2, similarity
    WITH gds.util.asNode(node1) AS user, gds.util.asNode(node2) AS similar_user, similarity
    MATCH (similar_user)-[:WATCHED]->(movie:Movie)
    WHERE NOT (user)-[:WATCHED]->(movie)
    RETURN movie.title AS recommendation, similarity
    ORDER BY similarity DESC
    LIMIT 5;
    """
    result = session.run(query, user_id=user_id)
    return [record["recommendation"] for record in result]

# Function for content-based recommendations using GDS
def get_content_based_recommendations(user_id, session):
    query = """
    MATCH (u:User {id: $user_id})-[:WATCHED]->(m1:Movie)
    WITH u, m1
    MATCH (m2:Movie)-[r:SIMILAR]->(m1)
    RETURN m2.title AS recommendation, r.similarity AS score
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

        # Create similarity relationships for content_based
        create_similarity_relationships(session)

        # Try collaborative filtering
        print(f"Getting recommendations for User {user_id} using Collaborative Filtering...")
        recommendations = get_collaborative_recommendations(user_id, session)
        # recommendations = []

        # Fallback to content-based filtering if no recommendations
        if not recommendations:
            print(f"No collaborative recommendations found. Falling back to Content-Based Filtering...")
            recommendations = get_content_based_recommendations(user_id, session)

        # Return recommendations
        return recommendations

# Entry point
if __name__ == "__main__":
    try:
        user_id = 2 # Example user ID
        recommendations = get_recommendations(user_id)
        print(f"Recommendations for User {user_id}: {recommendations}")
    finally:
        driver.close()
