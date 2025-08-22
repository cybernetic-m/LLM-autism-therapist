import sys
import os
import threading
import queue
import uuid

from flask import Flask, request, render_template, jsonify, redirect, url_for, session


sys.path.insert(0, './audio')
sys.path.insert(0, './neo4j_db')
sys.path.insert(0, './llm')
sys.path.insert(0, './face')
app = Flask(__name__)

# Check the operating system, it is used for the import modules
if os.name == 'nt':  # 'nt' stands for Windows
    from neo4j_db.database import KnowledgeGraph
    from audio.audio import record_audio
    from audio.audio_api import audio_groq_api
    from llm.TherapistLLM import TherapistLLM
    from llm.DatabaseLLM import DatabaseLLM
    #from face.face_main import face_thread
    with open("../llm/api_key.txt", "r") as file:
        groq_api_key = file.read()

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from database import KnowledgeGraph
    from audio import record_audio
    from audio_api import audio_groq_api
    from TherapistLLM import TherapistLLM
    from DatabaseLLM import DatabaseLLM
    from face_main import face_thread
    with open("./llm/api_key.txt", "r") as file:
        groq_api_key = file.read()


# _____ VARIABLES AND UTILS _____
therapist_model = 'llama-3.3-70b-versatile'
db_model = 'gemma2-9b-it' # from 8 October 2025 SHOULD CHANGE TO 'llama-3.1-8b-instant'
whisper_model_name = 'whisper-large-v3'
stop = ''

active_chats = {} # gestisce le chat attive sul server per vari utenti
app.secret_key = "super_secret_key_change_me" # gestisce sessioni flask

# Create a stop event object for the face thread
#stop_event = threading.Event()
# Create a queue for the results of the thread execution
#q = queue.Queue()
# Create the face thread
#thread_face = threading.Thread(target=face_thread, args=(q,stop_event))


kg = KnowledgeGraph()
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
therapist = TherapistLLM(model_name=therapist_model)
db_llm = DatabaseLLM(api_key=groq_api_key, model_name=db_model)
FORM_LINK = 'https://forms.gle/dZcZWoxQqcNBP9zE8'

# Pagina iniziale
@app.route('/')
def index():
    return render_template('index.html')

# Check is the child is new or already registered
@app.route('/check_child', methods=['POST'])
def check_child():
    data = request.get_json()
    name = data.get('name')
    surname = data.get('surname')

    all_children = kg.get_child(name=name, surname=surname)

    if len(all_children) == 0:
        # new child
        return jsonify({'askSex': True, 'askBirth': True})
    elif len(all_children) > 1:
        # More than one child with the same name and surname
        return jsonify({'askSex': False, 'askBirth': True})
    else:
        # the child exist in the database
        return jsonify({'askSex': False, 'askBirth': False, 'child': all_children[0]})

# submit of data from home page
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    surname = request.form.get('surname')
    sex = request.form.get('sex')
    birth = request.form.get('birth')
    modality = request.form.get('modality')

    if not sex: # the child exists
        if birth:
            child = kg.get_child(name=name, surname=surname, birth_date=birth)
        else:
            child = kg.get_child(name=name, surname=surname)

        app.logger.info(f"child={child}")
        child = child[0]
        data = {
            "child_name": child["Name"],
            "child_surname": child["Surname"],
            "child_birth": child["Birth"],
            "child_gender": child["Gender"],
            "child_nation": child.get("Nation"),
            "child_likes": child["LIKES"],
            "child_dislikes": child["DISLIKES"],
            "previous_activity": child.get("last_activity"),
            }
    else: # the child is new
        data = unknown_child
        data["child_name"] = name
        data["child_surname"] = surname
        data["child_gender"] = sex


    # save child data in the session
    session["child_data"] = data
    session["chat_id"] = str(uuid.uuid4())  # id unique for chat session
    therapist = TherapistLLM(model_name=therapist_model)
    therapist.load_data(data)

    # save the therapist in the session
    active_chats[session["chat_id"]] = therapist

    app.logger.info(f"{data}")

    if modality == 'chat':
        return render_template('chat.html', child=data)
    return render_template('chat_voice.html', child=data)


# when the chat starts the therapist begins the conversation
@app.route("/chat/start")
def chat_start():
    chat_id = session.get("chat_id")
    therapist = active_chats.get(chat_id)

    if not therapist:
        return jsonify({"error": "Sessione non trovata"}), 400

    first_message = therapist.speak()
    return jsonify({"robot": first_message})


# handles when the child sends a message
@app.route("/chat/send_message", methods=["POST"])
def chat_message():
    chat_id = session.get("chat_id")
    therapist = active_chats.get(chat_id)

    if not therapist:
        return jsonify({"error": "Sessione non trovata"}), 400

    data = request.get_json()
    response = data.get("message")

    therapist.add_child_response(response)
    return jsonify({"child": response, "robot": therapist.speak()})

# handles chat exit and data savings
@app.route("/chat/exit", methods=["POST"])
def chat_exit():
    chat_id = session.get("chat_id")
    data = session.get("child_data", {})
    therapist = active_chats.pop(chat_id, None)  # remove therapist
    #stop_event.set()
    #thread_face.join()
    #score = q.get()  # obtain the queue values (in our case only the score)

    score = 0 # ELIMINARE


    if therapist:
        data_db_llm = (
            "[CHILD INFO]:\n"
            f"name: {data['child_name']}\n"
            f"surname: {data['child_surname']}\n"
            f"birth: {data['child_birth']}\n"
            f"[CONVERSATION]: {therapist.session_history}"
        )

        app.logger.info(f"exit from chat -> {data_db_llm}")
        db_llm.save_info(conversation=data_db_llm, verbose=True, score=score)

    session.clear() # clear the session

    return jsonify({"link": FORM_LINK})



# when audio is sent by chat_voice.html
@app.route("/chat/send_audio", methods=["POST"])
def chat_audio():
    audio_file = request.files["audio"]
    # Salva temporaneamente
    audio_path = f"temp_audio_{session['chat_id']}.wav"
    audio_file.save(audio_path)

    # Trascrizione
    response_text = audio_groq_api(api_key=groq_api_key,
                                   model_name=whisper_model_name,
                                   audio_path=audio_path)

    app.logger.info(f"transcription -> {response_text}")

    chat_id = session.get("chat_id")
    therapist_instance = active_chats.get(chat_id)
    if therapist_instance is None:
        return jsonify({"error": "Therapist non trovato"}), 400

    therapist_instance.add_child_response(response_text)
    app.logger.info(f"therapist -> {therapist_instance.data}")

    return jsonify({
        "child": response_text,
        "robot": therapist_instance.speak()
    })

if __name__ == '__main__':
    app.run(debug=True)

