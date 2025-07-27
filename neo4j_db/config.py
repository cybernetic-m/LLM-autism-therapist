from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).parent / "config.env"
load_dotenv(dotenv_path=env_path)

# NEO4J VARIABLES
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")



# DATABASE DATA
NODES = {
    "Child": ["Id", "Name", "Surname", "Birth", "Gender", "Nation"],
    "Activity": ["Id", "Name"],
    "ActivityDetail": ["Genre", "Summary"]
}

RELATIONSHIPS = [
    {"type": "LIKES", "from": "Child", "to": "ActivityDetail", "properties": ["score", "date"]},
    {"type": "DISLIKES", "from": "Child", "to": "ActivityDetail", "properties": ["score", "date"]},
    {"type": "SUBCLASS_OF", "from": "ActivityDetail", "to": "Activity"}
]

ACTIVITIES = ["Storytelling", "Music"]
