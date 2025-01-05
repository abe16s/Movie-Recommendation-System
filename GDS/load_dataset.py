import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Load datasets
movies = pd.read_csv("movies_metadata.csv", low_memory=False)
ratings = pd.read_csv("ratings_small.csv")

# Preprocess movies metadata
movies = movies[['id', 'title', 'release_date', 'genres']].dropna()
movies['release_year'] = pd.to_datetime(movies['release_date']).dt.year
movies['genres'] = movies['genres'].apply(lambda x: [g['name'] for g in eval(x)] if isinstance(x, str) else [])

# Function to load data into Neo4j
def load_movies_and_users():
    with driver.session() as session:
        # Create movies
        for _, row in movies.iterrows():
            session.run(
                """
                CREATE (m:Movie {id: $id, title: $title, release_year: $release_year, genres: $genres})
                """,
                id=row['id'],
                title=row['title'],
                release_year=row['release_year'],
                genres=row['genres'],
            )

        # Create users and their relationships
        for _, row in ratings.iterrows():
            session.run(
                """
                MERGE (u:User {id: $user_id})
                MERGE (m:Movie {id: $movie_id})
                CREATE (u)-[:WATCHED {rating: $rating, timestamp: $timestamp}]->(m)
                """,
                user_id=row['userId'],
                movie_id=row['movieId'],
                rating=row['rating'],
                timestamp=row['timestamp'],
            )

# Run data loading
load_movies_and_users()
print("Data successfully loaded into Neo4j.")
