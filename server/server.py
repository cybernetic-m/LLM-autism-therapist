import sys
import os
import threading
import queue
import uuid
import glob

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
    from gtts import gTTS
    #from face.face_main import face_thread
    with open("../llm/api_key.txt", "r") as file:
        groq_api_key = file.read()

elif os.name == 'posix':  # 'posix' stands for Unix/Linux/MacOS
    from database import KnowledgeGraph
    from audio_api import audio_groq_api
    from TherapistLLM import TherapistLLM
    from DatabaseLLM import DatabaseLLM
    from gtts import gTTS
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

def get_audio_response(robot_text, chat_id):
    """Generate unique audio file with gTTS to avoid cache issues."""
    cleanup_all_audio()
    unique_id = uuid.uuid4().hex

    # File system path (per salvare il file)
    file_name = f"audio_{chat_id}_{unique_id}.mp3"
    file_path = os.path.join(app.root_path, "static", file_name)
    print(f"Saving audio to {file_path}")

    tts = gTTS(robot_text, lang="it")
    tts.save(file_path)

    # Web path (per farlo leggere dal browser)
    return f"/static/{file_name}"


def cleanup_all_audio():
    static_dir = os.path.join(app.root_path, "static")
    # Cerca tutti i file audio con estensioni comuni
    audio_extensions = ("*.mp3", "*.wav", "*.ogg", "*.m4a")

    for ext in audio_extensions:
        pattern = os.path.join(static_dir, ext)
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.warning(f"Failed to remove {file_path}: {e}")

# Homepage
@app.route('/')
def index():
    return render_template('index.html')


# Check if the child is already registered or new
@app.route('/check_child', methods=['POST'])
def check_child():
    data = request.get_json()
    name = data.get('name')
    surname = data.get('surname')

    all_children = kg.get_child(name=name, surname=surname)

    if len(all_children) == 0:
        # No child found → new child
        return jsonify({'askSex': True, 'askBirth': True})
    elif len(all_children) > 1:
        # Multiple children with same name → ask for birth date
        return jsonify({'askSex': False, 'askBirth': True})
    else:
        # Child already exists
        return jsonify({'askSex': False, 'askBirth': False, 'child': all_children[0]})


# Submit child data from home page
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    surname = request.form.get('surname')
    sex = request.form.get('sex')
    birth = request.form.get('birth')
    modality = request.form.get('modality')

    if not sex:  # Existing child
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
    else:  # New child
        data = unknown_child
        data["child_name"] = name
        data["child_surname"] = surname
        data["child_gender"] = sex

    # Save child info and chat session
    session["child_data"] = data
    session["chat_id"] = str(uuid.uuid4())
    therapist = TherapistLLM(model_name=therapist_model)
    therapist.load_data(data)

    # Store active therapist instance
    active_chats[session["chat_id"]] = therapist

    app.logger.info(f"{data}")

    return render_template('chat_voice.html', child=data, mode=modality)


# Start the chat → therapist speaks first
@app.route("/chat/start")
def chat_start():
    chat_id = session.get("chat_id")
    therapist = active_chats.get(chat_id)

    if not therapist:
        return jsonify({"error": "Session not found"}), 400

    first_message = therapist.speak()
    audio_path = get_audio_response(first_message, chat_id)
    return jsonify({"robot": first_message, "robot_audio": f"{audio_path}"})


# Handle text messages from the child
@app.route("/chat/send_message", methods=["POST"])
def chat_message():
    chat_id = session.get("chat_id")
    therapist = active_chats.get(chat_id)

    if not therapist:
        return jsonify({"error": "Session not found"}), 400

    data = request.get_json()
    response = data.get("message")

    therapist.add_child_response(response)
    robot_text = therapist.speak()
    audio_path = get_audio_response(robot_text, chat_id)
    return jsonify({"child": response, "robot": robot_text, "robot_audio": f"{audio_path}"})


# Handle chat exit and save data to DB
@app.route("/chat/exit", methods=["POST"])
def chat_exit():
    chat_id = session.get("chat_id")
    data = session.get("child_data", {})
    therapist = active_chats.pop(chat_id, None)  # remove therapist instance

    score = 0  # TODO: compute actual score

    if therapist:
        data_db_llm = (
            "[CHILD INFO]:\n"
            f"name: {data['child_name']}\n"
            f"surname: {data['child_surname']}\n"
            f"birth: {data['child_birth']}\n"
            f"previous activity: {data['previous_activity']}"
            f"[CONVERSATION]: {therapist.session_history}"
        )

        app.logger.info(f"exit from chat -> {data_db_llm}")
        db_llm.save_info(conversation=data_db_llm, verbose=True, score=score)

    session.clear()  # clear session after exit
    cleanup_all_audio()

    return jsonify({"link": FORM_LINK})

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads", "temp")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Handle audio messages from the child
@app.route("/chat/send_audio", methods=["POST"])
def chat_audio():
    audio_file = request.files["audio"]
    audio_path = f"static/user_audio_{session['chat_id']}.wav"
    audio_file.save(audio_path)

    # Transcribe with Whisper/Groq API
    response_text = audio_groq_api(
        api_key=groq_api_key,
        model_name=whisper_model_name,
        audio_path=audio_path
    )

    app.logger.info(f"transcription -> {response_text}")

    chat_id = session.get("chat_id")
    therapist_instance = active_chats.get(chat_id)
    if therapist_instance is None:
        return jsonify({"error": "Therapist not found"}), 400

    therapist_instance.add_child_response(response_text)
    app.logger.info(f"therapist -> {therapist_instance.data}")

    robot_text = therapist_instance.speak()
    audio_path = get_audio_response(robot_text, chat_id)
    return jsonify({"child": response_text, "robot": robot_text, "robot_audio": f"{audio_path}"})

if __name__ == '__main__':
    app.run(debug=True)

