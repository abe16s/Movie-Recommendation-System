# Movie Recommendation System

This is a movie recommendation system based collaborative and content based recommendation using Neo4j graph database for building graphs with nodes and relationships and recommending users, movies that they may like.

Create a ```.env``` file with your Neo4j database configurations on the `root` directory
```
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
```

## Basic collaborative and content based recommendation

### ```Basic_recommendation``` directory

* ```populate.txt``` Use the Cypher queries to populate your Neo4j database with custom users and movies data.

* ```recommendation.py``` defined a ```MovieRecommendationSystem``` class with content_based_recommendation and collaborative_filtering_recommendation.


## Graph Data Science (GDS) recommendation

### ```GDS``` directory

* Two datasets downloaded from [kaggle](https://www.kaggle.com/code/rounakbanik/movie-recommender-systems/input?select=movies_metadata.csv) ```movies_metadata.csv``` and ```ratings_small.csv``` that contain movies and ratings data.

* ```load_dataset``` Preprocess the Datasets and load the datasets to Neo4j database.

* ```gds_cypher.txt``` Cypher queries for creating the graph projection for GDS, use Neo4j’s Graph Data Science (GDS) library for collaborative filtering and content-based filtering as a fallback on Neo4j database.  

* Or alternatively use the ```GDS_setup.py``` for creating  the graph projection for GDS

* ```recommendation.py``` python script for getting recommendation using collaborative filtering as main and content-based as a fallback.


#### Install python packages dependencies

```pip install neo4j python-dotenv```

