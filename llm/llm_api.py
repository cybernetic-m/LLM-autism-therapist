import requests
import time
from typing import Optional
from neo4j_db.database import KnowledgeGraph
import ast
from datetime import datetime

from dotenv import load_dotenv
import os
from pathlib import Path
import sys

from llm.llm_config import SYSTEM_PROMPT_DATABASE_LLM, SYSTEM_PROMPT_THERAPIST, USER_PROMPT_TEMPLATE_THERAPIST

env_path = Path(__file__).parent / "api.env"
load_dotenv(dotenv_path=env_path)
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("API KEY NOT LOADED")
    sys.exit(1)

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
    def __init__(self, api_key):
        self.api_key = api_key
        self.system_prompt = SYSTEM_PROMPT_DATABASE_LLM
        self.kg = KnowledgeGraph()

    def save_info(self, child_id, conversation = '', verbose = False, score = None):

        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name="gemma2-9b-it",
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

            parsed = ast.literal_eval(line)

            fn = parsed["function"]
            data = parsed["data"]

            if not isinstance(data, dict):
                raise TypeError("Expected 'data' to be a dictionary")

            # Post-process data if needed
            if fn == "add_child_node":
                if "Birth" in data:
                    data["Birth"] = datetime.date.fromisoformat(data["Birth"])
                data["Id"] = child_id  # Add or assign a unique ID
                self.kg.add_child_node(data)

            elif fn == "add_activity" and score:
                self.kg.add_activity(
                    childID=child_id,  # Match to correct child ID
                    genre=data["Genre"],
                    summary=data["Summary"],
                    score=score,
                    activityClass="Storytelling"
                )



class TherapistLLM:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT_THERAPIST
        self.user_prompt = USER_PROMPT_TEMPLATE_THERAPIST
        self.session_history = ''


    def calculate_age(birth_date_str, today=None):
        # birth_date_str should be in "YYYY-MM-DD" format
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        if today is None:
            today = datetime.today().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age

    def speak(self, data):
        formatted_user_prompt = self.user_prompt.format(
            child_name=data['name'],
            child_surname=data['surname'],
            child_age=self.calculate_age(data['birth']),
            child_gender=data['gender'],
            child_nation=data['nation'],
            child_likes=data['child_likes'],
            child_dislikes = data['dislikes'],
            previous_activity=data['previous_activity'],
            conversation_history=self.session_history
        )
        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name="gemma2-9b-it",
                                            system_prompt_template=self.system_prompt,
                                            user_prompt_template=formatted_user_prompt,
                                            temperature=0.0)

        return llm_response



known_child = {
    "child_name": "Sofia",
    "child_surname": "Bianchi",
    "child_birth": "2016-09-12",
    "child_gender": "Female",
    "child_nation": "Italy",
    "child_likes": "Fairy tales, drawing, singing Disney songs",
    "child_dislikes": "dinosaurs",
    "previous_activity": "Storytelling about a magical forest with unicorns",
    "conversation_history": "You: Hi Sofia! Last time we visited a magical forest. Would you like to go back there or try something new? Sofia: I want a new story with a dragon!"
}

if __name__ == '__main__':
     therapist = TherapistLLM()
     data = known_child
     print(therapist.speak(data))




