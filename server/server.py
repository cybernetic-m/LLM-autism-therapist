import sys
import os
import threading
import queue
import uuid
import glob
from pydub import AudioSegment
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
    from face_main import face_thread
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
stop_event = threading.Event()
# Create a queue for the results of the thread execution
q = queue.Queue()
# Create the face thread
thread_face = threading.Thread(target=face_thread, args=(q,stop_event))

chat_id = "test"

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
db_llm = DatabaseLLM(api_key=groq_api_key, model_name=db_model)
FORM_LINK = 'https://forms.gle/dZcZWoxQqcNBP9zE8'
last_response_audio_length = 0


def get_audio_response(robot_text, chat_id):
    cleanup_all_audio()
    unique_id = uuid.uuid4().hex
    file_name = f"audio_{chat_id}_{unique_id}.mp3"
    file_path = os.path.join(app.root_path, "static", file_name)

    tts = gTTS(robot_text, lang="it")
    tts.save(file_path)

    audio = AudioSegment.from_file(file_path)
    duration_seconds = round(len(audio) / 1000, 2)

    # salva nella sessione
    session['last_response_audio_length'] = duration_seconds

    return f"/static/{file_name}", duration_seconds


def cleanup_all_audio():
    """deletes all audios in the static"""
    static_dir = os.path.join(app.root_path, "static")
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


# Check if the child is already registered or new during the index.html process
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
        data["child_birth"] = birth

    # Save child info and chat session
    session["child_data"] = data
    session["chat_id"] = chat_id #str(uuid.uuid4())
    therapist = TherapistLLM(model_name=therapist_model)
    therapist.load_data(data)

    # Store active therapist instance
    active_chats[session["chat_id"]] = therapist

    app.logger.info(f"{data}") # prints

    return render_template('chat_voice.html', child=data) # MODE = MODALITY REMOVED CHECK IF ERRORS

def get_therapist_response(chat_id = None, child_message = None):
    therapist = active_chats.get(chat_id) # retrieves the therapist of this session

    if not therapist:
        print("error: Session not found")

    if child_message:
        therapist.add_child_response(child_message)

    robot_response = therapist.speak()
    # makes the mp3 audio and returns the path for javascript
    audio_path, duration = get_audio_response(robot_response, chat_id)

    return robot_response, audio_path, duration


# Start the chat → therapist speaks first
@app.route("/chat/start")
def chat_start():
    chat_id = session.get("chat_id")
    message, audio_path, duration = get_therapist_response(chat_id)

    #thread_face.start()
    return jsonify({"robot": message, "robot_audio": f"{audio_path}", "chat_id": chat_id})


# Handle text messages from the child
@app.route("/chat/send_message", methods=["POST"])
def chat_message():
    chat_id = session.get("chat_id")

    data = request.get_json()
    response = data.get("message") # get the message sent

    robot_response, audio_path, duration = get_therapist_response(chat_id, response)

    return jsonify({"child": response, "robot": robot_response, "robot_audio": f"{audio_path}"})


# Handle chat exit and save data to DB
@app.route("/chat/exit", methods=["POST"])
def chat_exit():
    chat_id = session.get("chat_id")
    data = session.get("child_data", {})
    therapist = active_chats.pop(chat_id, None)  # remove therapist instance

    # Stop the face thread at the end of the conversation
    stop_event.set()
    #thread_face.join()
    try:
        score = q.get_nowait()
    except Exception:
        score = 0  # default se non c'è niente in coda

    #score = 0

    if therapist:
        data_db_llm = (
            "[CHILD INFO]:\n"
            f"name: {data['child_name']}\n"
            f"surname: {data['child_surname']}\n"
            f"birth: {data['child_birth']}\n"
            f"previous activity: {data['previous_activity']}\n"
            f"[CONVERSATION]: {therapist.session_history}"
        )

        app.logger.info(f"exit from chat -> {data_db_llm}")
        # save the info in the db
        db_llm.save_info(conversation=data_db_llm, verbose=True, score=score)

    session.clear()  # clear session after exit
    cleanup_all_audio() # clean all audio in static folder

    return jsonify({"link": FORM_LINK})



# Handle audio messages from the child
@app.route("/chat/send_audio", methods=["POST"])
def chat_audio():
    audio_file = request.files["audio"]  # get the audio from browser

    # Path
    audio_path = os.path.join(app.root_path, "static", f"user_audio_{session['chat_id']}.wav")
    audio_file.save(audio_path)  # save it

    # Transcribe with Whisper/Groq API
    response_text = audio_groq_api(
        api_key=groq_api_key,
        model_name=whisper_model_name,
        audio_path=audio_path
    )

    # retrieve therapist
    chat_id = session.get("chat_id")
    robot_response, audio_path, duration = get_therapist_response(chat_id, response_text)


    # ma al client conviene dare il path relativo (così il browser può scaricarlo da /static)
    robot_audio_url = f"/static/{os.path.basename(audio_path)}"

    return jsonify({
        "child": response_text,
        "robot": robot_response,
        "robot_audio": robot_audio_url
    })

@app.route('/send_data', methods=['GET'])
def send_data():
    print("send_data called")
    try:
        chat_id = request.args.get("chat_id")  # The Robot Client passes chat_id as a query parameter
        if not chat_id:
            raise ValueError("chat_id is required")
        therapist = active_chats.get(chat_id)  # Use chat_id to retrieve the session's therapist
        if not therapist:
            raise ValueError(f"No active chat session found for chat_id: {chat_id}")
        sentence = therapist.last_response
        gesture = therapist.last_gesture
        t = session.get('last_response_audio_length', 0)
        print(f"Sending to robot: sentence={sentence}, gesture={gesture}, t={t}")
        return jsonify({"sentence": sentence, "gesture": gesture, "t": t})
    except Exception as e:
        print(f"Error in send_data: {e}")
        return jsonify({"sentence": "", "gesture": "", "t": 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

