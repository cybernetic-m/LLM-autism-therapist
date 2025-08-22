import math
import qi
import argparse

class Robot:
    
    def __init__(self, ip, port):
        
        # Start of the session => The connection with Choreographe/Naoqi services
        self.session = self.initConnection(ip, port)
        # Initialization of the Pepper services:
        # -  motion service: allow to move the joint of the robot 
        # -  posture_service: allow to make the robot go to different postures ['Crouch', 'LyingBack', 'Sit',...]
        # -  animation_service: allow to start predefined animations [eg. gestures Hey_1 to hello]
        # -  tts_service: the TextToSpeech service allows the robot to speak
        self.motion_service = self.session.service("ALMotion")
        self.tts_service = self.session.service("ALTextToSpeech")
        self.animation_service = self.session.service("ALAnimationPlayer")
        self.ans_service = self.session.service("ALAnimatedSpeech")
        self.posture_service = self.session.service("ALRobotPosture")


    def initConnection(self, ip, port):
        '''
        Method to init the connection using the IP address of the robot and the port for the TCP communication
        Args:
        ip (str): the IP address of the robot
        port (int): the port of communication (IMPORTANT: you should check after opening choreographe in Edit/Preferences/Virtual Robot)
        '''
        try:
            connection_url = "tcp://" + ip + ":" + str(port)
            app = qi.Application(["Therapist", "--qi-url=" + connection_url])   # create the application object that is the bridge from our code to Choreographe
            print("Connection to the Robot at IP:"+ip+" at port "+ str(port) +" OK")

        except RuntimeError:
            print("Connection to the Robot at IP:+"+ip+" at port "+port+" FAILED. Try to change IP/PORT or to run Choregraphe correctly. Please follow the READMe instructions correctly.")
            exit()

        app.start() #start the connection
        session = app.session

        return session
    
    def say(self, sentence, t):

        '''
        This method having a sentence and the time that I want to display in Choreographe, then display the sentence
        Args:
            - sentence (str): the sentence to display
            - t (int): time to display the sentence in seconds
        '''
        
        # k_pause is a constant =  N/t where N is the number of ' ' spaces in a time interval
        # I have experimentally computed it putting 25 spaces and observing 7 s of time displaying the sentence in Choreographe
        k_pause = 3.5
        n_spaces = int(k_pause * t) # number of spaces needed to wait t time for my sentence
        pause = " " * n_spaces  # effectively the string '     ' 

        self.tts_service.say(sentence+ pause)

    def hello_gesture(self):
        
        # Defining the name of the joints, the times of each joint motion and the variable is absolute for absolute values
        joint_names = ['LElbowRoll', 'LElbowYaw', 'LHand', 'LShoulderPitch', 'LShoulderRoll', 'LWristYaw', 'RElbowRoll', 'RElbowYaw', 'RHand', 'RShoulderPitch', 'RShoulderRoll', 'RWristYaw']
        times  = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        isAbsolute = True

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(joint_names, angles_start, times, isAbsolute)
        
        # Say Hello motion
        angles_t1 = [math.radians(-50.7), math.radians(-86.5), 0.98, math.radians(-3.6), math.radians(41.6), math.radians(12.5), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        self.motion_service.angleInterpolation(joint_names, angles_t1, times, isAbsolute)
        angles_t2 = [math.radians(-78.1), math.radians(-86.5), 0.98, math.radians(-3.6), math.radians(41.6), math.radians(12.5), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        self.motion_service.angleInterpolation(joint_names, angles_t2, times, isAbsolute)
        angles_t3 = [math.radians(-30), math.radians(-86.5), 0.98, math.radians(-3.6), math.radians(41.6), math.radians(12.5), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        self.motion_service.angleInterpolation(joint_names, angles_t3, times, isAbsolute)        
        
        # Returning to starting state
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(joint_names, angles_start, times, isAbsolute)




if __name__ == "__main__":
    # Argument Terminal Parser, you need to execute the code using "python Robot.py -ip {your_ip} -port {your_port}"
    parser = argparse.ArgumentParser(description="Robot IP and Port")
    parser.add_argument("-ip", type=str, default='127.0.0.1', help="IP address of the robot (e.g., 127.0.0.1)")
    parser.add_argument("-port", type=int, required=True,  help="Port for communication (e.g., 36439)")

    # Parse the arguments
    args = parser.parse_args()

    robot = Robot(ip=args.ip, port=args.port)
    robot.say("Ciao a tutti", t=5)
    robot.hello_gesture()

