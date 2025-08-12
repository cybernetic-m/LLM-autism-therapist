import sys
sys.path.insert(0, './audio') 
sys.path.insert(0, './neo4j_db') 
sys.path.insert(0, './llm')

import requests
import time
from typing import Optional
from database import KnowledgeGraph
import ast
from datetime import datetime
import yaml
#from dotenv import load_dotenv
import os
from pathlib import Path

from audio import record_audio, speech2text

#env_path = Path(__file__).parent / "api.env"
#load_dotenv(dotenv_path=env_path)
#groq_api_key = os.getenv("GROQ_API_KEY")

with open("llm/api_key.txt", "r") as file:
    groq_api_key = file.read()

if not groq_api_key:
    print("API KEY NOT LOADED: please follow the instructions in the README.md file to set up the API key.")
    sys.exit(1)

with open("llm/config.yaml", "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)

system_prompt_db = prompts["system_prompts"]["database_llm"]
system_prompt_therapist = prompts["system_prompts"]["therapist"]
user_prompt_therapist = prompts["user_prompt_templates"]["therapist"]


def call_translation_api(api_key, model_name, system_prompt_template, user_prompt_template, temperature) -> Optional[
    str]:
    # This function sends a Prompt to a Groq-hosted API waiting for the response (the translated sentence)
    # Args: - api_key: the Groq API key you need to authorization
    #       - model_name: the name of the LLM model (ex. "llama-3.1-8b-instant")
    #       - system_prompt_template: <str> it is a prompt containing the instructions for the model (ex. "You are a translator...")
    #       - user_prompt_template: <str> it is a prompt containing the sentence to translate
    #       - temperature: <float> it is a float number to set the temperature of the model
    # Output: - translation: <str> the translated sentence returned by the model, or None if an error occurred

    url = "https://api.groq.com/openai/v1/chat/completions"  # this is the url of the Groq API (same structure of OpenAI message!)

    # The header of the message contain the "Content-Type" (it say that the message structure will be json, a dict) and the "Authorization"
    # It is a string "Bearer gsk...." with the api_key in a Bearer Token type (Bearer means that the authorization is give with the api_key directly after)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # This is the message content itself. It contain the "model_name", its "temperature"
    # the messages contain two dictionaries: the first one is the system prompt (the instructions for the model, like "You are a translator...")
    # and the second one is the user prompt (the input sentence to translate)
    data = {
        "model": model_name,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": system_prompt_template
            },
            {
                "role": "user",
                "content": user_prompt_template
            }
        ]
    }

    while True:
        try:
            response = requests.post(url, headers=headers, json=data)  # send the request to the Groq API
            # Check for rate limiting (HTTP 429), wait 5 seconds and retry
            if response.status_code in [429, 500]:
                # print(f"Received {response.status_code}. Retrying in 5s...")
                time.sleep(5)
                continue  # Retry after wait

            response.raise_for_status()  # Raise an exception for other HTTP errors like 400 or 500 (if one occurred)
            translation = response.json()  # return the response in json format (a dict)

            # Translation is a dict with 'id' (a unique identifier for the request),  'created' (the timestamp of the request) ...
            # inside 'choices' there are different generated responses in general, we take the first one
            # inside 'choices there is the 'message' (translation) with the 'role' (user or assistant) and the 'content' (the translated sentence with the reasoning)
            return translation["choices"][0]["message"]["content"].strip()

        except requests.exceptions.RequestException as e:
            print(f"Request failed for: '{user_prompt_template}'\nError: {e}")
            return None



class DatabaseLLM:
    def __init__(self, api_key, model_name = 'deepseek-r1-distill-llama-70b'):
        self.api_key = api_key
        self.system_prompt = system_prompt_db
        self.kg = KnowledgeGraph()
        self.model_name = model_name

    def save_info(self, conversation = '', verbose = False, score = 0):

        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name=self.model_name,
                                            system_prompt_template=self.system_prompt,
                                            user_prompt_template=conversation,
                                            temperature=0.0)
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
                        activityClass="Storytelling"
                    )

            except Exception as e:
                print("Error in line:", line, "error:", e)


class TherapistLLM:
    def __init__(self, model_name = 'deepseek-r1-distill-llama-70b'):
        self.system_prompt = system_prompt_therapist
        self.user_prompt = user_prompt_therapist
        self.session_history = ''
        self.data = None
        self.model_name = model_name

    def load_data(self, data):
        self.data = data

    def calculate_age(self, birth_date_str, today=None):
        # birth_date_str should be in "YYYY-MM-DD" format
        if birth_date_str == '':
            return ''

        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        if today is None:
            today = datetime.today().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age

    def add_child_response(self, response):
        self.session_history += '\n -Child:' + response

    def speak(self):
        formatted_user_prompt = self.user_prompt.format(
            child_name=self.data['child_name'],
            child_surname=self.data['child_surname'],
            child_age=self.calculate_age(data['child_birth']),
            child_gender=self.data['child_gender'],
            child_nation=self.data['child_nation'],
            child_likes=self.data['child_likes'],
            child_dislikes = self.data['child_dislikes'],
            previous_activity=self.data['previous_activity'],
            conversation_history=self.session_history
        )
        #print("FORMATTED PROMPT:\n ______________________ \n" + formatted_user_prompt + '\n ___________________')
        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name=self.model_name,
                                            system_prompt_template=self.system_prompt,
                                            user_prompt_template=formatted_user_prompt,
                                            temperature=1)
        self.session_history += '\n -Therapist: ' + llm_response
        return llm_response



known_child = {
    "child_name": "Sofia",
    "child_surname": "Romero",
    "child_birth": "2016-09-12",
    "child_gender": "Female",
    "child_nation": "Italy",
    "child_likes": "Fairy tales, drawing, singing Disney songs",
    "child_dislikes": "dinosaurs",
    "previous_activity": "",
}


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

if __name__ == '__main__':

    therapist_model = 'llama3-70b-8192'
    db_model = 'gemma2-9b-it'

    name = input("Hi! What's your name? ")
    surname = input("And your surname? ")

    kg = KnowledgeGraph()
    all_data = kg.get_child(name=name, surname=surname)

    data = None
    if len(all_data) == 0:
        data = unknown_child
    elif len(all_data) > 1:
        birth = input("Can you also tell me your birthdate?")
    else:
        child = all_data[0]
        data = {
                "child_name": child["Name"],
                "child_surname": child["Surname"],
                "child_birth": child["Birth"],
                "child_gender": child["Gender"],
                "child_nation": child.get("Nation"), # may be missing and return None
                "child_likes": child["LIKES"],
                "child_dislikes": child["DISLIKES"],
                "previous_activity": child.get("last_activity"),
            }
    print(data)
    therapist = TherapistLLM(model_name=therapist_model)
    therapist.load_data(data)
    print(therapist.speak())

    while True:
        record_audio()  # Call the function to record audio
        response = speech2text("audio.wav", model_size='medium')  # Call the function to transcribe the recorded audio
        if response == '0': break
        therapist.add_child_response(response)
        print("- THERAPIST:\n" + therapist.speak())


    db_llm = DatabaseLLM(api_key=groq_api_key, model_name=db_model)
    data_db_llm = '[CHILD INFO]:\n' + "name: " + data["child_name"] + "\nsurname: " + data["child_surname"] + "\nbirth: " + data["child_birth"] + "\n" + "[CONVERSATION]:" + therapist.session_history
    print(data_db_llm)
    db_llm.save_info(conversation= data_db_llm, verbose=True, score=0)






