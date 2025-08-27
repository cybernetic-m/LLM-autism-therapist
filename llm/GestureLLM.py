import sys
import uuid

sys.path.insert(0, './llm')
import os
from datetime import datetime
import yaml
import os

# Check the operating system, it is used for the import modules
if os.name == 'nt':  # 'nt' stands for Windows
    from llm.llm_api import call_translation_api

    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "api_key.txt")
    with open(file_path, "r") as file:
        groq_api_key = file.read()
    with open("../config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from llm_api import call_translation_api
    with open("llm/api_key.txt", "r") as file:
        groq_api_key = file.read()
    with open("config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)


if not groq_api_key:
    print("API KEY NOT LOADED: please follow the instructions in the README.md file to set up the API key.")
    sys.exit(1)

system_prompt_therapist = prompts["system_prompts"]["gesture_llm"]

class GestureLLM:
    def __init__(self, model_name):
        self.system_prompt = system_prompt_therapist
        self.last_gesture = ''
        self.model_name = model_name

    def get_gesture(self, child_sentence, therapist_response):
        prompt = "[CHILD SENTENCE]:" + child_sentence + " [ROBOT SENTENCE]: " + therapist_response + " [LAST GESTURE]: " + self.last_gesture
        llm_response = call_translation_api(api_key=groq_api_key,
                                            model_name=self.model_name,
                                            system_prompt_template=self.system_prompt,
                                            user_prompt_template=prompt,
                                            temperature=0)
        return llm_response.split("[GESTURE]: ")[1]

