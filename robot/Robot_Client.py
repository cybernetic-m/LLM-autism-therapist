import sys
sys.path.insert(0, './robot')

import requests
import time
from Robot import Robot
import argparse

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

    while True:
        try:
            # Get the data from the server
            response = requests.get(server_url)
            if response.status_code == 200: # Check if the request was successful
                data = response.json() # Get the json data from the response 
                print("Data received from server: ", data)
                
                # Extract the sentence, gesture and time from the data
                sentence = data.get("sentence", "") # sentence is the text that the robot will say (default is empty)
                gesture = data.get("gesture", "")   # gesture is the gesture that the robot will do (default is empty)
                t = data.get("time", 5)   # time is the time that the robot will take to say the sentence and do the gesture (default is 5 seconds)

                robot.speak_and_move(sentence, gesture, t)

            # Wait for a short period before checking again
            time.sleep(1)
 
        except Exception as e:
            print("An error occurred: " + str(e))

if __name__ == "__main__":
    main()

   