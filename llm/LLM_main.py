import sys
import os
import threading
import queue
sys.path.insert(0, './audio') 
sys.path.insert(0, './neo4j_db') 
sys.path.insert(0, './llm')
sys.path.insert(0, './face')

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="whisper")
sys.stderr = open(os.devnull, 'w')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")


# Check the operating system, it is used for the import modules
if os.name == 'nt':  # 'nt' stands for Windows
    from neo4j_db.database import KnowledgeGraph
    from audio.audio import record_audio, speech2text
    from audio.audio_api import audio_groq_api
    from llm.TherapistLLM import TherapistLLM
    from llm.DatabaseLLM import DatabaseLLM
    from face.face_main import face_thread
    with open("api_key.txt", "r") as file:
        groq_api_key = file.read()

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from database import KnowledgeGraph
    from audio import record_audio
    from audio_api import audio_groq_api
    from TherapistLLM import TherapistLLM
    from DatabaseLLM import DatabaseLLM
    from face_main import face_thread
    with open("llm/api_key.txt", "r") as file:
        groq_api_key = file.read()


if not groq_api_key:
    print("API KEY NOT LOADED: please follow the instructions in the README.md file to set up the API key.")
    sys.exit(1)


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


therapist_model = 'llama-3.3-70b-versatile'
db_model = 'gemma2-9b-it' # from 8 October 2025 SHOULD CHANGE TO 'llama-3.1-8b-instant'
whisper_model_name = 'whisper-large-v3'
stop = ''

# Create a stop event object for the face thread
stop_event = threading.Event()
# Create a queue for the results of the thread execution
q = queue.Queue()

# Create the face thread
thread_face = threading.Thread(target=face_thread, args=(q,stop_event))

print("Ciao! Inserisci il tuo nome:")
name = input("")
print("Inserisci il tuo cognome:")
surname = input("")
print("Premi 1 se vuoi parlare, 2 se vuoi chattare:")
modality = input("")
if not (modality == '1' or modality == '2'):
    print("Error: hai scelto una modalità non valida!!! Scegli la '1' o la '2'.")
    exit()

kg = KnowledgeGraph()
all_data = kg.get_child(name=name, surname=surname)

data = None
if len(all_data) == 0:
    data = unknown_child
    data["child_name"] = name
    data["child_surname"] = surname
    print("Puoi specificare il tuo sesso? Scrivi 'Uomo' o 'Donna'")
    sex = input("")
    if sex == 'Uomo' or sex == 'Donna':
        data["child_gender"] = sex
    else:
        print("Error: Hai specificato un sesso errato! Per favore scrivi 'Uomo' o 'Donna'.")
        exit()
elif len(all_data) > 1:
    print("Puoi specificare la tua data di nascita (formato dd/mm/yyyy)?")
    birth = input("")
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
#print(data)
therapist = TherapistLLM(model_name=therapist_model)
therapist.load_data(data)

# Start the face thread before the interaction
thread_face.start()

print("\n-TERAPISTA:\n" + therapist.speak() +'\n')

while True:
    if modality == '1':
        print("Parla ... per interrompere la registrazione premi Ctrl+C.")
        record_audio()  # Call the function to record audio
        response = audio_groq_api(api_key = groq_api_key, model_name = whisper_model_name, audio_path = 'audio.wav')
    else:
        print("- TU (per interrompere la conversazione scrivi 'q'): ")
        response = input("")

    therapist.add_child_response(response)

    print("\n-TERAPISTA:\n" + therapist.speak()+'\n')
    
    if modality == '1':
        print("")
        stop = input("Premi 'q' per interrompere la conversazione o qualsiasi altro tasto per continuare: ")

    if stop.lower() == 'q' or response=='q':
        print("Terapia terminata.")
        break

# Stop the face thread at the end of the conversation
stop_event.set()
thread_face.join()
score = q.get() # obtain the queue values (in our case only the score)

db_llm = DatabaseLLM(api_key=groq_api_key, model_name=db_model)
data_db_llm = '[CHILD INFO]:\n' + "name: " + data["child_name"] + "\nsurname: " + data["child_surname"] + "\nbirth: " + data["child_birth"] + "\n" + "[CONVERSATION]:" + therapist.session_history
#print(data_db_llm)
db_llm.save_info(conversation= data_db_llm, verbose=True, score=score)






