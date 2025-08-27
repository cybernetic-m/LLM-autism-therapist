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
    from llm.GestureLLM import GestureLLM

    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "api_key.txt")
    with open(file_path, "r") as file:
        groq_api_key = file.read()
    with open("../config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from llm_api import call_translation_api
    from GestureLLM import GestureLLM
    with open("llm/api_key.txt", "r") as file:
        groq_api_key = file.read()
    with open("config/llm_config.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)


if not groq_api_key:
    print("API KEY NOT LOADED: please follow the instructions in the README.md file to set up the API key.")
    sys.exit(1)

system_prompt_therapist = prompts["system_prompts"]["therapist"]
user_prompt_therapist = prompts["user_prompt_templates"]["therapist"]

class TherapistLLM:
    def __init__(self, model_name):
        self.system_prompt = system_prompt_therapist
        self.user_prompt = user_prompt_therapist
        self.session_history = ''
        self.data = None
        self.model_name = model_name
        self.last_gesture = ''
        self.last_response = ''
        self.gesture_llm = GestureLLM(model_name='gemma2-9b-it')

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
            child_age=self.calculate_age(self.data['child_birth']),
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
        self.last_response = llm_response
        self.last_gesture = self.gesture_llm.get_gesture(llm_response) # get the gesture from the response
        return llm_response

    def export_conversation(self, path='conversations'):
        """
        Esporta la conversazione in un file di testo con un ID univoco.
        Compatibile sia con Windows che con Linux/Mac.
        """
        # Creiamo una cartella "conversations" se non esiste
        os.makedirs(path, exist_ok=True)

        # Creiamo un ID univoco
        unique_id = str(uuid.uuid4())

        # Nome file con timestamp + ID
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}.txt"

        # Percorso completo
        file_path_conversation = os.path.join(path, filename)

        # Salviamo il contenuto
        with open(file_path_conversation, "w", encoding="utf-8") as file_conv:
            file_conv.write("Therapy Session Conversation\n\n")
            file_conv.write(self.session_history.strip())

        return file_path_conversation

