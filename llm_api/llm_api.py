import requests
import time
from typing import Optional
from neo4j_db.database import KnowledgeGraph
import ast
import datetime
import random
from dotenv import load_dotenv
import os
from pathlib import Path
import sys

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

SYSTEM_PROMPT = """
You are a robot talking to a child. You must extract and store the following structured information when available:

CHILD:
- Name, Surname, Birth (date), Gender, Nation

ACTIVITY (like storytelling):
- Genre (e.g., Fantasy), Summary

Use the following functions to save data to the knowledge graph:
1. add_child_node
2. add_activity

During the conversation, once you have all the required data for a child or activity, make a python dictionary with the appropriate function and with the correct values using this format: {"function": "function_name", "data": "data for the function" (e.g: {"function": "add_child_node", "data": {"Name": "Paolo", "Surname": "Renzi", "Birth": datetime.date(2012, 5, 10), "Gender": "Male", "Nickname": "Pablo Escobar", "Nation": "Italy"}} and/or {"function": "add_activity", "data": {genre="Romantic", summary="story about a fish that sings}})
Return only the raw formatted text, do not put any other formatting like markdowns or quotes except the ones asked.
"""

CONV_1 = """Robot: Hello there! What’s your name?
Child: I’m Antonio.
Robot: Nice to meet you Antonio. What’s your last name?
Child: Lissa.
Robot: Do you have a nickname your friends call you?
Child: Yeah, they call me Provola.
Robot: That’s a funny one! When were you born?
Child: On May 10th, 2008.
Robot: Got it! Are you a boy or a girl?
Child: I’m a boy.
Robot: Where are you from?
Child: I’m from Italy!
Robot: Would you like to tell me a story today?
Child: Yes! I want to tell a fantasy story.
Robot: Oh cool! What is it about?
Child: It's about a singing horse who wants to become a pop star.
Robot: That’s amazing!
"""


CONV_2 = """Robot: Hello there! What’s your name? 
Child: I’m Sofia.
Robot: Nice to meet you Sofia. What’s your last name?
Child: Romero.
Robot: Do you have a nickname your friends call you?
Child: Yes, they call me Fifi!
Robot: That’s a sweet one! When were you born?
Child: On October 22nd, 2011.
Robot: Got it! Are you a boy or a girl?
Child: I’m a girl.
Robot: Where are you from?
Child: I’m from Argentina!
Robot: Would you like to tell me a story today?
Child: Yes! I want to tell a mystery story.
Robot: Oh cool! What is it about?
Child: It's about a cat detective who solves the case of the missing cupcakes.
Robot: That’s amazing!
"""



if __name__ == '__main__':
    kg = KnowledgeGraph()
    kg.erase_graph()


    llm_response = call_translation_api(api_key=groq_api_key,
                         model_name="gemma2-9b-it",
                         system_prompt_template=SYSTEM_PROMPT,
                         user_prompt_template=CONV_2,
                         temperature=0.0)
    print(llm_response)

    ID = random.randint(0, 9999999)
    for line in llm_response.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        #print("line: ", line)

        parsed = ast.literal_eval(line)

        fn = parsed["function"]
        data = parsed["data"]

        if not isinstance(data, dict):
            raise TypeError("Expected 'data' to be a dictionary")

        # Post-process data if needed
        if fn == "add_child_node":
            if "Birth" in data:
                data["Birth"] = datetime.date.fromisoformat(data["Birth"])
            data["Id"] = ID  # Add or assign a unique ID
            kg.add_child_node(data)

        elif fn == "add_activity":
            kg.add_activity(
                childID=ID,  # Match to correct child ID
                genre=data["Genre"],
                summary=data["Summary"],
                score=1,
                activityClass="Storytelling"
            )
