import sys
import time
import uuid

sys.path.insert(0, './llm')
sys.path.insert(0, './neo4j_db')
import os
from datetime import datetime
import yaml
import os
import random
from datetime import date, timedelta
import math

# Check the operating system, it is used for the import modules
if os.name == 'nt':  # 'nt' stands for Windows
    from llm.llm_api import call_translation_api
    from llm.TherapistLLM import TherapistLLM

    from llm.DatabaseLLM import DatabaseLLM
    from neo4j_db.database import KnowledgeGraph

    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "api_key.txt")
    with open(file_path, "r") as file:
        groq_api_key = file.read()
    with open("../config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from llm_api import call_translation_api
    from TherapistLLM import TherapistLLM
    from DatabaseLLM import DatabaseLLM
    from database import KnowledgeGraph

    with open("llm/api_key.txt", "r") as file:
        groq_api_key = file.read()
    with open("config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

if not groq_api_key:
    print("API KEY NOT LOADED: please follow the instructions in the README.md file to set up the API key.")
    sys.exit(1)

system_prompt = prompts["system_prompts"]["child_llm"]
user_prompt = prompts["user_prompt_templates"]["child_llm"]


class ChildLLM:
    def __init__(self, model_name):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.session_history = ''
        self.data = None
        self.model_name = model_name
        self.last_gesture = ''
        self.last_response = ''
        self.last_child_sentence = ''

    def respond(self, child_info, session_history):
        prompt = self.user_prompt.format(child_data=child_info, conversation_history=session_history)
        #print("-- FINAL PROMPT --\n", prompt)
        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name=self.model_name,
                                            system_prompt_template=self.system_prompt,
                                            user_prompt_template=prompt,
                                            temperature=1)

        self.session_history += '\n -Therapist: ' + llm_response
        self.last_response = llm_response
        return llm_response


unknown_child = {
    "child_name": "",
    "child_surname": "",
    "child_birth": "",
    "child_gender": "",
    "child_nation": "",
    "child_likes": "",
    "child_dislikes": "",
    "previous_activity": "",
}

names_male = ["Luca", "Marco", "Andrea", "Matteo", "Giovanni", "Antonio", "Massimo", "Paolo"]
names_female = ["Giulia", "Sara", "Chiara", "Martina", "Elisa"]
surnames = ["Rossi", "Bianchi", "Verdi", "Neri", "Gialli"]


def random_birthdate(start_year=2010, end_year=2022):
    """Genera una data di nascita casuale tra start_year e end_year."""
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    delta_days = (end_date - start_date).days
    birthdate = start_date + timedelta(days=random.randint(0, delta_days))
    return birthdate.strftime("%Y-%m-%d")


def get_random_child():
    sex = random.choice(["M", "F"])
    personalities = [
        # Positive
        "curious", "playful", "creative", "brave", "kind", "energetic"
        # Negative
        "stubborn", "lazy", "selfish", "impatient", "shy", "rebellious", "distracted"
    ]
    personality = random.choice(personalities)
    if sex == "M":
        name = random.choice(names_male)
    else:
        name = random.choice(names_female)
    surname = random.choice(surnames)
    birth = random_birthdate()
    return name, surname, sex, birth, personality


def get_score(start, increment):
    return str(round(abs(math.sin(start + increment)), 2))  # not negative sin

def make_childs(num):
    childs = []
    for i in range(num):
        childs.append(get_random_child())
    return childs

if __name__ == '__main__':

    childs = make_childs(50) # make 50 childs with name, surname, birthdate, sex and one personality trait
    conversation_length = 8

    for conv in range(2):  # make 100 conversations
        print(f"\n     --- CONVERSATION {conv} STARTING ---\n")
        child_llm = ChildLLM(model_name='gemma2-9b-it')
        name, surname, sex, birth, personality = random.choice(childs) # use a random child
        kg = KnowledgeGraph()
        all_data = kg.get_child(name=name, surname=surname)
        data = None
        if len(all_data) == 0:
            data = unknown_child
            data["child_name"] = name
            data["child_surname"] = surname
            data["child_gender"] = sex
            data["child_birth"] = birth
        elif len(all_data) > 1:
            print("Bambino già creato, riprova")
            exit()
        else:
            child = all_data[0]
            data = {
                "child_name": child["Name"],
                "child_surname": child["Surname"],
                "child_birth": child["Birth"],
                "child_gender": child["Gender"],
                "child_nation": child.get("Nation"),  # may be missing and return None
                "child_likes": child["LIKES"],
                "child_dislikes": child["DISLIKES"],
                "previous_activity": child.get("last_activity"),
            }

        print("-- CHILD DATA --\n", data)
        therapist = TherapistLLM(model_name='llama-3.3-70b-versatile')
        therapist.load_data(data)

        # score_start = random.uniform(0, 3.14) # simulate score
        # increment = random.uniform(0.1, 0.5)

        for i in range(conversation_length):
            therapist_response = therapist.speak()
            data['personality'] = personality
            child_response = child_llm.respond(data, therapist.session_history)
            therapist.add_child_response(child_response)  # + " [SCORE]: " + get_score(score_start, increment*i))


        db_llm = DatabaseLLM(api_key=groq_api_key, model_name='gemma2-9b-it')
        data_db_llm = '[CHILD INFO]:\n' + "name: " + data["child_name"] + "\nsurname: " + data[
            "child_surname"] + "\nbirth: " + data["child_birth"] + "\n" + "[CONVERSATION]:" + therapist.session_history

        print(data_db_llm)
        db_llm.save_info(conversation=data_db_llm, verbose=True, score=random.uniform(0, 1))
        therapist.export_conversation(other_info=db_llm.last_response)

        time.sleep(60)
