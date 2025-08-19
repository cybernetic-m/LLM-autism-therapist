import os
import yaml
# NEO4J VARIABLES
if os.name == 'nt':  # 'nt' stands for Windows
    with open("../config/db_config.yaml", "r", encoding="utf-8") as f:
            neo4j_data = yaml.safe_load(f)
if os.name == 'posix':  # 'posix' stands for Linux or macOS
    with open("config/db_config.yaml", "r", encoding="utf-8") as f:
            neo4j_data = yaml.safe_load(f)

NEO4J_URI = neo4j_data["NEO4J_URI"]
NEO4J_USERNAME = neo4j_data["NEO4J_USERNAME"]
NEO4J_PASSWORD = neo4j_data["NEO4J_PASSWORD"]

# DATABASE DATA
NODES = {
    "Child": ["Id", "Name", "Surname", "Birth"],
    "Activity": ["Id", "Name"],
    "ActivityDetail": ["Genre", "Summary"]
}

RELATIONSHIPS = [
    {"type": "LIKES", "from": "Child", "to": "ActivityDetail", "properties": ["score", "date"]},
    {"type": "DISLIKES", "from": "Child", "to": "ActivityDetail", "properties": ["score", "date"]},
    {"type": "SUBCLASS_OF", "from": "ActivityDetail", "to": "Activity"}
]

ACTIVITIES = ["Storytelling", "Music"]
