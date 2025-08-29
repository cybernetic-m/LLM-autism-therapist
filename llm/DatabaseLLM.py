import sys
sys.path.insert(0, './neo4j_db') 
sys.path.insert(0, './llm')
import os
import ast
import yaml
import os

# Check the operating system, it is used for the import modules
if os.name == 'nt':  # 'nt' stands for Windows
    from neo4j_db.database import KnowledgeGraph
    from llm.llm_api import call_translation_api
    with open("../llm/api_key.txt", "r") as file:
        groq_api_key = file.read()
    with open("../config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from database import KnowledgeGraph
    from llm_api import call_translation_api
    with open("llm/api_key.txt", "r") as file:
        groq_api_key = file.read()
    with open("config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

if not groq_api_key:
    print("API KEY NOT LOADED: please follow the instructions in the README.md file to set up the API key.")
    sys.exit(1)

system_prompt_db = prompts["system_prompts"]["database_llm"]

class DatabaseLLM:
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        self.system_prompt = system_prompt_db
        self.kg = KnowledgeGraph()
        self.model_name = model_name
        self.last_response = ''

    def save_info(self, conversation = '', verbose = False, score = 0):

        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name=self.model_name,
                                            system_prompt_template=self.system_prompt,
                                            user_prompt_template=conversation,
                                            temperature=0.0)

        self.last_response = llm_response
        if verbose:
            print(llm_response)

        #ID = random.randint(0, 9999999)
        for line in llm_response.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            # print("line: ", line)

            try:
                parsed = ast.literal_eval(line)
                fn = parsed["function"]
                data = parsed["data"]

                if not isinstance(data, dict):
                    raise TypeError("Expected 'data' to be a dictionary")

                # Post-process data if needed
                if fn == "add_child_node":
                    print("adding child")
                    self.kg.add_child_node(data)

                elif fn == "add_activity":
                    print("adding activity")
                    self.kg.add_activity(
                        name=data['name'],
                        surname=data['surname'],
                        birthdate=data['birthdate'],
                        genre=data["genre"],
                        summary=data["summary"],
                        score=score,
                        activityClass=data["activity_class"]
                    )

            except Exception as e:
                print("Error in line:", line, "error:", e)