from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os

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
    from face.face_main import face_thread
elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from database import KnowledgeGraph
    from audio import record_audio
    from audio_api import audio_groq_api
    from TherapistLLM import TherapistLLM
    from DatabaseLLM import DatabaseLLM
    from face_main import face_thread

from flask import Flask, request, render_template, jsonify, redirect, url_for

app = Flask(__name__)

# _____ utils _____
therapist_model = 'llama-3.3-70b-versatile'
db_model = 'gemma2-9b-it' # from 8 October 2025 SHOULD CHANGE TO 'llama-3.1-8b-instant'
whisper_model_name = 'whisper-large-v3'
stop = ''

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

# Pagina iniziale
@app.route('/')
def index():
    return render_template('index.html')

# Check se il bambino è registrato
@app.route('/check_child', methods=['POST'])
def check_child():
    data = request.get_json()
    name = data.get('name')
    surname = data.get('surname')

    all_children = kg.get_child(name=name, surname=surname)

    if len(all_children) == 0:
        # Bambino completamente nuovo → chiedi sesso
        return jsonify({'askSex': True, 'askBirth': True})
    elif len(all_children) > 1:
        # Più bambini con lo stesso nome → chiedi data di nascita
        return jsonify({'askSex': False, 'askBirth': True})
    else:
        # Esiste un solo bambino → nessun campo extra da chiedere
        return jsonify({'askSex': False, 'askBirth': False, 'child': all_children[0]})

# Submit dei dati
@app.route('/submit', methods=['POST'])
def submit():
    # Riceve i dati dal form
    name = request.form.get('name')
    surname = request.form.get('surname')
    sex = request.form.get('sex')
    birth = request.form.get('birth')
    modality = request.form.get('modality')

    if not sex: # bambino esistente
        if birth:
            data = kg.get_child(name=name, surname=surname, birth_date=birth)
        else:
            data = kg.get_child(name=name, surname=surname)
    else:
        data = unknown_child
        data["child_name"] = name
        data["child_surname"] = surname
        data["child_gender"] = sex


    therapist.load_data(data)
    return render_template('chat.html', child=data)
# Pagina chat
@app.route('/chat')
def chat():
    first_message = therapist.speak()
    return render_template("chat.html", first_message=first_message)
@app.route("/chat/send_message", methods=["POST"])
def chat_message():
    data = request.get_json()
    child_message = data.get("message")

    # qui userai TherapistLLM
    # per ora finta risposta:
    robot_reply = f"Hai detto: {child_message}. Interessante! 😊"

    return jsonify({"child": child_message, "robot": robot_reply})
if __name__ == '__main__':
    app.run(debug=True)

