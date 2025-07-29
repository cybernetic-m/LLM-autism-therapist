from neo4j import GraphDatabase
from neo4j_db.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NODES, RELATIONSHIPS, ACTIVITIES
import datetime
from neo4j.time import Date


class KnowledgeGraph:
    def __init__(self):
        self.URI = NEO4J_URI
        self.USER = NEO4J_USERNAME
        self.PASSWORD = NEO4J_PASSWORD
        self.nodes_properties = NODES
        self.activities = ACTIVITIES
        self.check()

        self.driver = GraphDatabase.driver(self.URI, auth=(self.USER, self.PASSWORD))
        self.check_connection()

        self.add_activity_updates() # just in case we added a new activity in the config.py

    def add_activity_updates(self):
        # adds the nodes in self.activities if they do not already exist
        for elem in self.activities:
            self.run_query(f'MERGE (a:Activity {{name: "{elem}"}})')

    def get_last_activity(self, name=None, surname=None, birth_date=None):
        query = """
        MATCH (c:Child)-[r]->(ad:ActivityDetail)
        WHERE ($name IS NULL OR c.Name = $name)
          AND ($surname IS NULL OR c.Surname = $surname)
          AND ($birth_date IS NULL OR c.Birth = $birth_date)
          AND type(r) IN ['LIKES', 'DISLIKES']
        RETURN
               ad.Genre AS activity_genre,
               ad.Summary AS activity_summary
        ORDER BY r.date DESC
        LIMIT 1
        """
        params = {
            "name": name,
            "surname": surname,
            "birth_date": birth_date
        }

        results = self.run_query(query, params or {})
        return {"last_activity": results[0]} if results else None

    def get_child(self, name=None, surname=None, birth_date=None):
        if not name and not surname and not birth_date:
            # No filters — return all children
            query = """
            MATCH (c:Child)
            RETURN properties(c) AS child
            """
            params = {}
        else:
            # Apply filters conditionally
            query = """
            MATCH (c:Child)
            WHERE ($name IS NULL OR c.Name = $name)
              AND ($surname IS NULL OR c.Surname = $surname)
              AND ($birth_date IS NULL OR c.Birth = $birth_date)
            RETURN properties(c) AS child
            """
            params = {
                "name": name,
                "surname": surname,
                "birth_date": birth_date
            }

        results = self.run_query(query, params or {})

        child_info = []
        for record in results:
            name = record['child']["Name"]
            surname = record["child"]["Surname"]
            birth = record["child"]["Birth"]
            child_preferences = self.get_child_preferences(name=name, surname=surname, birth_date=birth)
            last_activity = self.get_last_activity(name=name, surname=surname, birth_date=birth)
            if child_preferences:
                record['child'].update(child_preferences)
            if last_activity:
                record['child'].update(last_activity)
            child_info.append(record["child"])

        return child_info

    def get_child_preferences(self, name=None, surname=None, birth_date=None):
        query = """
        MATCH (c:Child)-[r]->(ad:ActivityDetail)-[:SUBCLASS_OF]->(a:Activity)
        WHERE ($name IS NULL OR c.Name = $name)
          AND ($surname IS NULL OR c.Surname = $surname)
          AND ($birth_date IS NULL OR c.Birth = $birth_date)
          AND type(r) IN ['LIKES', 'DISLIKES']
        RETURN type(r) AS relation_type,
               ad.Genre AS activity_genre,
               ad.Summary AS activity_summary,
               a.name AS activity_class
        """
        params = {
            "name": name,
            "surname": surname,
            "birth_date": birth_date
        }

        results = self.run_query(query, params or {})

        preferences = {"LIKES": [], "DISLIKES": []}
        for record in results:
            relation = record["relation_type"]
            entry = {
                "genre": record.get("activity_genre"),
                "summary": record.get("activity_summary"),
                "class": record.get("activity_class")
            }
            if relation in preferences:
                preferences[relation].append(entry)

        return preferences

    def check(self):
        # check if the env variables passed to the class are well defined
        if not self.URI or not self.USER or not self.PASSWORD:
            raise ValueError("Error: missing NEO4J_URI or USER or NEO4J_PASSWORD")

    def check_connection(self):
        #  check connection to the db
        try:
            conn_result = self.run_query("RETURN 'Connection OK' AS status")
            print(conn_result[0]['status'])
        except Exception as e:
            print("Connection failed:", e)

    def run_query(self, query, parameters=None):
        # executes any query passed as string with optional params
        #print("running query", query)
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
        query = f"MERGE (n:{label} {{ {props} }}) RETURN n"
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
        MERGE (start)-[r:{relationship_name}{rel_props}]->(end)
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
        if len(self.get_child(name=params['Name'], surname = params['Surname'], birth_date=params['Birth'])) == 0:
            print(" - adding node:", params)
            self.create_node("Child", params)
        else:
            print("node child already exist")
        '''if self.has_all_keys_with_values(params, self.nodes_properties['Child']):
            self.create_node("Child", params)
        else:
            print("Warning: the provided params for child are incomplete")'''

    def add_activity_detail_node(self, params):
        # adds an activityDetail node with params
        if self.has_all_keys_with_values(params, self.nodes_properties['ActivityDetail']):
            self.create_node("ActivityDetail", params)
        else:
            print("Warning: the provided params for avtivity detail are incomplete")

    def add_relationship_child_activity_detail(self, childID = None, name= None, surname= None, birthdate = None, activityDetailProperties= None, score= None, activityNodeName= None):
        # connects child to a new activity and the new activity to its class
        relation = 'LIKES' if score > 0 else 'DISLIKES'

        if childID is not None:
            start_node_match = {"Id": childID}
        elif name and surname and not birthdate:
            start_node_match = {"Name": name, "Surname": surname}
        elif name and surname and birthdate:
            start_node_match = {"Name": name, "Surname": surname, "Birth": birthdate}
        else:
            return

        if not score:
            score = ''

        self.create_relationship(
            start_node_label="Child",
            start_node_match=start_node_match,
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

    def add_activity(self, childID = None, name = None, surname = None, birthdate = None, genre = None, summary = None, score = None, activityClass = None):
        # adds an activity and builds the relationships with the child and the activity class
        print(f"    -Adding activity: childID={childID}, name={name}, surname={surname}, birthdate={birthdate}, genre={genre}, summary={summary}, score={score}, activityClass={activityClass}")
        activity_properties = {"Genre": genre, "Summary": summary}
        self.add_activity_detail_node(activity_properties)
        self.add_relationship_child_activity_detail(childID=childID,
                                                    name = name,
                                                    surname = surname,
                                                    birthdate = birthdate,
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
    kg = KnowledgeGraph()
    kg.erase_graph()

    # Create two nodes with a custom unique property 'id'
    kg.add_child_node({"Id": 0,
                       "Name": "Massimo",
                       "Surname": "Romano",
                       "Birth": "2010-08-16",
                       "Gender": "Female",
                       "Nickname": "Pappone",
                       "Nation": "Italy"})

    kg.add_child_node({"Id": 1,
                       "Name": "Paolo",
                       "Surname": "Renzi",
                       "Birth": "2012-05-10",
                       "Gender": "Male",
                       "Nickname": "Pablo Escobar", "Nation": "Italy"})

    # saves a new child
    kg.add_child_node({"Id": 2,
                       "Name": "Antonio",
                       "Surname": "Lissa",
                       "Birth": "2008-05-10",
                       "Gender": "Male",
                       "Nickname": "Provola", "Nation": "Italy"})


    # saves a new activity of a child
    kg.add_activity(childID=0, genre="Fantasy", summary="story about a singing horse", score=1,
                    activityClass="Storytelling" )
    kg.add_activity(childID=0, genre="Pop", summary="singing baby shark", score=0.8,
                    activityClass="Music")

    kg.add_activity(childID=1, genre="Horror", summary="story about a ghost named peter", score=-.1,
                    activityClass="Storytelling")

    kg.add_activity(childID=2, genre="Romantic", summary="story about a fish", score=-.1,
                    activityClass="Storytelling")
    kg.add_activity(childID=2, genre="Cartoon", summary="singing dragon ball", score=.5,
                    activityClass="Music")
    kg.add_activity(childID=2, genre="Adventure", summary="story of a dinosaur that goes missing", score=.8,
                    activityClass="Storytelling")


    result = kg.run_query("MATCH (start_node)-[relation]->(end_node) RETURN start_node,relation,end_node")

    for elem in result:
        print(elem['relation'])

    # Close the connection cleanly
    kg.close()




if __name__ == "__main__":
    kg_test()

    kg = KnowledgeGraph()
    #kg.add_activity(name= "marco", surname= "bomba", birthdate="2015-09-20", genre= "Fantasy", summary= "story about a fog", score = 0, activityClass="Storytelling" )

    #print(kg.get_child())


    print(kg.get_child(name = 'Massimo', surname = 'Romano'))


