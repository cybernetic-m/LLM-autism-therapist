import sys
sys.path.insert(0, './robot')

import requests
import time
from Robot import Robot
import argparse
import threading
from flask import Flask, request, jsonify

# Flask app for session handling
robot_app = Flask(__name__)
# Global variable to store current chat_id
current_chat_id = None

@robot_app.route('/start_session', methods=['POST'])
def start_session():
    global current_chat_id
    data = request.get_json()
    current_chat_id = data.get("chat_id")
    print(">>> Received start_session request with data:" + {data})
    print("Chat session initialized! Chat ID:", current_chat_id)
    return jsonify({"success": True})

def main():
   
    # Argument Terminal Parser, you need to execute the code using "python Robot.py -ip {your_ip} -port {your_port}"
    parser = argparse.ArgumentParser(description="Robot IP and Port")
    parser.add_argument("-ip", type=str, default='127.0.0.1', help="IP address of the robot (e.g., 127.0.0.1)")
    parser.add_argument("-port", type=int, required=True,  help="Port for communication (e.g., 36439)")

    # Parse the arguments
    args = parser.parse_args()

    # Create the Robot instance
    robot = Robot(ip=args.ip, port=args.port)

    # Create the server url
    server_url = "http://127.0.0.1:5000/send_data"

    # Run the Flask app in a separate thread to handle session sync
    threading.Thread(target=lambda: robot_app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False)).start()

    # Initialize print count and exception count to print only the first time that we enter in the try or except
    # Each time that we enter in the try or except the other counter is reset to 0
    print_try_count = 0
    print_exc_count = 0

    while True:
        try:   
            if current_chat_id:
                print_exc_count = 0 # reset the exception print count to print the exception message again

                # Print only the first time
                if print_try_count == 0:
                    print("Robot Client is listening on the server ", server_url)
                    print_try_count += 1

                # Get the data from the server
                response = requests.get(server_url+'?chat_id='+current_chat_id)
                if response.status_code == 200: # Check if the request was successful
                    data = response.json() # Get the json data from the response 
                    print("Data received from server: ", data)
                    
                    # Extract the sentence, gesture and time from the data
                    sentence = data.get("sentence", "") # sentence is the text that the robot will say (default is empty)
                    gesture = data.get("gesture", "")   # gesture is the gesture that the robot will do (default is empty)
                    t = data.get("time", 5)   # time is the time that the robot will take to say the sentence and do the gesture (default is 5 seconds)

                    robot.speak_and_move(sentence, gesture, t)
            else:
                print("Waiting for chat session to be initialized...")
                print_try_count = 0

            # Wait for a short period before checking again
            time.sleep(1)
 
        except Exception as e:
            if print_exc_count == 0:
                print("An error occurred: " + str(e))
                print_exc_count += 1
            print_try_count = 0 # reset the print count to print the listening message again

if __name__ == "__main__":
    main()

   