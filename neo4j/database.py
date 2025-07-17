from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NODES, RELATIONSHIPS, ACTIVITIES
import datetime



class KnowledgeGraph:
    def __init__(self, URI, USERNAME, PASSWORD):
        self.URI = URI
        self.USER = USERNAME
        self.PASSWORD = PASSWORD
        self.nodes_properties = NODES
        self.activities = ACTIVITIES
        self.check()

        self.driver = GraphDatabase.driver(self.URI, auth=(self.USER, self.PASSWORD))
        self.check_connection()

    def check(self):
        # check if the env variables passed to the class are well defined
        if not self.URI or not self.USER or not self.PASSWORD:
            raise ValueError("Error: missing URI or USER or PASSWORD")

    def check_connection(self):
        #  check connection to the db
        try:
            conn_result = self.run_query("RETURN 'Connection OK' AS status")
            print(conn_result[0]['status'])
        except Exception as e:
            print("Connection failed:", e)

    def run_query(self, query, parameters=None):
        # executes any query passed as string with optional params
        try:
            with self.driver.session() as my_session:
                query_result = my_session.run(query, parameters or {})
                return [record.data() for record in query_result]
        except Exception as e:
            print(f"Query failed: {e}")
            return None

    def create_node(self, label, properties, verbose=False):
        # makes a node
        props = ", ".join(f"{k}: ${k}" for k in properties)
        query = f"CREATE (n:{label} {{ {props} }}) RETURN n"
        if verbose:
            print("- Building node")
            print(" - query:", query)
        return self.run_query(query, properties)

    def create_relationship(self, start_node_label, start_node_match, end_node_label, end_node_match, relationship_name,
                            relationship_properties, verbose=False):
        """
        Creates a relationship between two nodes by specifying properties for matching.

        Parameters:
        - start_node_label: label (type) of the start node
        - start_node_match: dictionary with properties to match the start node (e.g., {"id": "123"})
        - end_node_label: label (type) of the end node
        - end_node_match: dictionary with properties to match the end node (e.g., {"id": "456"})
        - relationship_name: type of the relationship (e.g., "KNOWS")
        - relationship_properties: optional dictionary with properties for the relationship

        Returns:
        - List of dictionaries containing the result of the query.
        """

        # Helper function to build the WHERE clause for node matching
        def build_match(alias, match):
            return " AND ".join([f"{alias}.{k} = ${alias}_{k}" for k in match])

        # Prepare parameters for query, prefixing keys to avoid collisions
        parameters = {}
        parameters.update({f"start_{k}": v for k, v in start_node_match.items()})
        parameters.update({f"end_{k}": v for k, v in end_node_match.items()})
        parameters.update({f"rel_{k}": v for k, v in (relationship_properties or {}).items()})

        # Prepare relationship properties string if any properties are provided
        rel_props = ""
        if relationship_properties:
            rel_props = " { " + ", ".join([f"{k}: $rel_{k}" for k in relationship_properties]) + " }"

        # Cypher query string with MATCH on both nodes, WHERE clause, and CREATE relationship
        query = f"""
        MATCH (start:{start_node_label}), (end:{end_node_label})
        WHERE {build_match('start', start_node_match)} AND {build_match('end', end_node_match)}
        CREATE (start)-[r:{relationship_name}{rel_props}]->(end)
        RETURN type(r)
        """

        query_result = self.run_query(query, parameters)

        if verbose:
            print("- Building relationship")
            print("    - query params: ", parameters)
            print("    - query: ", query)

        return query_result

    def has_all_keys_with_values(self, d, keys):
        # checks if the dictionary has all keys of the keys list
        return all(key in d and d[key] not in (None, '', [], {}, ()) for key in keys)

    def add_child_node(self, params):
        # adds a child node with params
        if self.has_all_keys_with_values(params, self.nodes_properties['Child']):
            self.create_node("Child", params)
        else:
            print("Warning: the provided params for child are incomplete")

    def add_activity_detail_node(self, params):
        # adds an activityDetail node with params
        if self.has_all_keys_with_values(params, self.nodes_properties['ActivityDetail']):
            self.create_node("ActivityDetail", params)
        else:
            print("Warning: the provided params for avtivity detail are incomplete")

    def add_relationship_child_activity_detail(self, childID, activityDetailProperties, score, activityNodeName):
        # connects child to a new activity and the new activity to its class

        relation = 'LIKES' if score > 0 else 'DISLIKES'
        self.create_relationship(
            start_node_label="Child",
            start_node_match={"Id": childID},
            end_node_label="ActivityDetail",
            end_node_match=activityDetailProperties,
            relationship_name=relation,
            relationship_properties={"score": score, "date": datetime.datetime.now()},
            verbose=False
        )

        self.create_relationship(
            start_node_label="ActivityDetail",
            start_node_match=activityDetailProperties,
            end_node_label="Activity",
            end_node_match={"Id": self.activities.index(activityNodeName)},
            relationship_name="SUBCLASS_OF",
            relationship_properties={},
            verbose=False
        )

    def add_activity(self, childID, genre, summary, score, activityClass):
        # adds an activity and builds the relationships with the child and the activity class
        activity_properties = {"Genre": genre, "Summary": summary}
        self.add_activity_detail_node(activity_properties)
        self.add_relationship_child_activity_detail(childID=childID,
                                                    activityDetailProperties=activity_properties,
                                                    score=score,
                                                    activityNodeName=activityClass)

    def erase_graph(self):
        # erase all the informations in the graph
        erase = input("Do you want to erase all the informations stored in the graph? [y/n] ")
        if erase.lower() == 'y':
            query = "MATCH (n) DETACH DELETE n"
            self.run_query(query)
            self.build_all_activities() # rebuilds activities

    def build_all_activities(self):
        # rebuilds all activities that are saved in the config.py file, the id corresponds to the position in the list
        # this is useful if the graph was erased
        for elem in self.activities:
            self.create_node("Activity", {"Id": self.activities.index(elem), "name": elem})

    def close(self):
        self.driver.close()


def kg_test():
    # Instantiate the KnowledgeGraph with connection details
    kg = KnowledgeGraph(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    kg.erase_graph()

    # Create two nodes with a custom unique property 'id'
    kg.add_child_node({"Id": 0,
                       "Name": "Massimo",
                       "Surname": "Romano",
                       "Birth": datetime.date(2010, 8, 16),
                       "Gender": "Female",
                       "Nickname": "Pappone",
                       "Nation": "Italy"})

    kg.add_child_node({"Id": 1,
                       "Name": "Paolo",
                       "Surname": "Renzi",
                       "Birth": datetime.date(2012, 5, 10),
                       "Gender": "Male",
                       "Nickname": "Pablo Escobar", "Nation": "Italy"})

    kg.add_activity(childID=0, genre="Fantasy", summary="story about a singing horse", score=1,
                    activityClass="Storytelling" )
    kg.add_activity(childID=0, genre="Pop", summary="singing baby shark", score=0.8,
                    activityClass="Music")
    kg.add_activity(childID=1, genre="Horror", summary="story about a ghost named peter", score=-.1,
                    activityClass="Storytelling")


    result = kg.run_query("MATCH (start_node)-[relation]->(end_node) RETURN start_node,relation,end_node")

    for elem in result:
        print(elem['relation'])

    # Close the connection cleanly
    kg.close()


USEFUL_QUERIES = {
    "get_everything":
    """
    MATCH (s)-[r]->(e)
    RETURN 
      properties(s) AS start_node,
      type(r) AS rel_type,
      properties(r) AS rel_props,
      properties(e) AS end_node
    """,
    "get_node_by_id": """
        MATCH (n:{label} {{id: $id}})
        RETURN n
    """,
    "get_nodes_with_relationship": """
        MATCH (start:{start_label})-[relationship:{rel_type}]->(end:{end_label})
        RETURN start, relationship, end
    """,

    "delete_node_by_id": """
        MATCH (n:{label} {{id: $id}})
        DETACH DELETE n
    """,

    "update_node_properties": """
        MATCH (n:{label} {{id: $id}})
        SET n += $properties
        RETURN n
    """
}


if __name__ == "__main__":

    kg_test()

    '''kg = KnowledgeGraph(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    query_template = USEFUL_QUERIES["get_node_by_id"].format(label="Child")
    params = {"id": 0}
    result = kg.run_query(query_template, params)
    print(result)

    query_template = USEFUL_QUERIES["get_nodes_with_relationship"].format(start_label = 'Child',
                                                                            rel_type = 'LIKES',
                                                                            end_label = 'Activity')
    result = kg.run_query(query_template)
    print(result)

    query_template = USEFUL_QUERIES["get_everything"]
    result = kg.run_query(query_template)
    for elem in result:
        print(elem)

    kg.close()'''

