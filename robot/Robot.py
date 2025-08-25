# coding=utf-8
import math
import threading
import qi
import argparse
import time

class Robot:
    
    def __init__(self, ip, port):
        
        # Start of the session => The connection with Choreographe/Naoqi services
        self.session = self.initConnection(ip, port)
        
        # Initialization of the Pepper services:
        # -  motion service: allow to move the joint of the robot 
        # -  tts_service: the TextToSpeech service allows the robot to speak
        self.motion_service = self.session.service("ALMotion")
        self.tts_service = self.session.service("ALTextToSpeech")

        # Definition of a list of all joints of right and left arms
        self.joint_names = ['LElbowRoll', 'LElbowYaw', 'LHand', 'LShoulderPitch', 'LShoulderRoll', 'LWristYaw', 'RElbowRoll', 'RElbowYaw', 'RHand', 'RShoulderPitch', 'RShoulderRoll', 'RWristYaw']
        self.isAbsolute = True  # boolean to set all the movements in an absolute reference frame
        self.head = ['HeadPitch', 'HeadYaw']  # list of head joints

        # Init of the list of gestures that the robot can do
        self.admitted_gestures = ["hello_gesture_1", "hello_gesture_2", "moving_gesture_single_arm", "moving_gesture_double_arm", "approval_gesture", "disapproval_gesture", "surprise_gesture", "thinking_gesture"]

        # Set the robot to the starting state of joints
        self.homing()

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


    def homing(self):
        
        # Defining the times of each joint motion 
        times  = [0.4, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        
        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        

    def hello_gesture_1(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        
        # Say Hello motion
        angles_t1 = [math.radians(-50.7), math.radians(-86.5), 0.98, math.radians(-3.6), math.radians(41.6), math.radians(12.5), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
        angles_t2 = [math.radians(-78.1), math.radians(-86.5), 0.98, math.radians(-3.6), math.radians(41.6), math.radians(12.5), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)
        angles_t3 = [math.radians(-30), math.radians(-86.5), 0.98, math.radians(-3.6), math.radians(41.6), math.radians(12.5), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        self.motion_service.angleInterpolation(self.joint_names, angles_t3, times, self.isAbsolute)        
        
        # A second round
        self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)
        self.motion_service.angleInterpolation(self.joint_names, angles_t3, times, self.isAbsolute)        

        # Returning to starting state
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)

    def hello_gesture_2(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        
        # Say Hello motion
        angles_t1 = [math.radians(-85.1), math.radians(-114.4), 0.98, math.radians(48.0), math.radians(21.6), math.radians(20.0), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
        angles_t2 = [math.radians(-65.5), math.radians(-114.4), 0.98, math.radians(48.0), math.radians(21.6), math.radians(20.0), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)
        
        # A second round
        self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
        self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)        

        # Returning to starting state
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)

    def moving_gesture_single_arm(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        time_ref = time.time()  # reference time to check the time t of the motion

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        
        # angles needed for this motion
        angles_t1 = [math.radians(-55.2), math.radians(-88.4), 0.98, math.radians(30.3), math.radians(9.6), math.radians(-69.7), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        angles_t2 = [math.radians(-41.5), math.radians(-88.4), 0.98, math.radians(30.3), math.radians(9.6), math.radians(-69.7), math.radians(84.3), math.radians(61.4), 0.93, math.radians(118.5), math.radians(-34.0), math.radians(-11.5)]
        
        # Loop until the say method is finished (time t)
        # I check if the time t is finished to stop the motion, really I use 75% of the time t to be sure that the motion is finished before the say method
        while (time.time() - time_ref) < t*0.75:
            self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
            self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)      
        
        # Returning to starting state
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)

    def moving_gesture_double_arm(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        time_ref = time.time()  # reference time to check the time t of the motion

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        
        # angles needed for this motion
        angles_t1 = [math.radians(-55.2), math.radians(-88.4), 0.98, math.radians(30.3), math.radians(9.6), math.radians(-69.7), math.radians(45.9), math.radians(100.6), 0.98, math.radians(60.6), math.radians(-7.9), math.radians(55.9)]
        angles_t2 = [math.radians(-41.5), math.radians(-88.4), 0.98, math.radians(30.3), math.radians(9.6), math.radians(-69.7), math.radians(37.9), math.radians(100.6), 0.98, math.radians(60.6), math.radians(-7.9), math.radians(55.9)]
        
        # Loop until the say method is finished (time t)
        # I check if the time t is finished to stop the motion, really I use 75% of the time t to be sure that the motion is finished before the say method
        while (time.time() - time_ref) < t*0.75:
            self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
            self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)      
        
        # Returning to starting state
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)

    def approval_gesture(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.5, 0.5]

        # Starting position
        angles_start = [math.radians(-21.6), math.radians(0.6)]
        self.motion_service.angleInterpolation(self.head, angles_start, times, self.isAbsolute)
        
        # angles needed for this motion
        angles_t1 = [math.radians(22.2), math.radians(0.6)]
        
        # I do two rounds to say yes with the head
        self.motion_service.angleInterpolation(self.head, angles_t1, times, self.isAbsolute)
        self.motion_service.angleInterpolation(self.head, angles_start, times, self.isAbsolute)      

        self.motion_service.angleInterpolation(self.head, angles_t1, times, self.isAbsolute)
        self.motion_service.angleInterpolation(self.head, angles_start, times, self.isAbsolute)      

    def disapproval_gesture(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.5, 0.5]

        # Starting position
        angles_start = [math.radians(-21.6), math.radians(0.6)]
        self.motion_service.angleInterpolation(self.head, angles_start, times, self.isAbsolute)
        
        # angles needed for this motion
        angles_t1 = [math.radians(22.2), math.radians(36.7)]
        angles_t2 = [math.radians(22.2), math.radians(-28.9)]
        
        # I do two rounds to say yes with the head
        self.motion_service.angleInterpolation(self.head, angles_t1, times, self.isAbsolute)
        self.motion_service.angleInterpolation(self.head, angles_t2, times, self.isAbsolute)      
        
        self.motion_service.angleInterpolation(self.head, angles_t1, times, self.isAbsolute)
        self.motion_service.angleInterpolation(self.head, angles_t2, times, self.isAbsolute)  
        
        # Returning to starting state
        self.motion_service.angleInterpolation(self.head, angles_start, times, self.isAbsolute)

    def surprise_gesture(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        time_ref = time.time()  # reference time to check the time t of the motion

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        
        # angles needed for this motion
        angles_t1 = [math.radians(-89.1), math.radians(-57.5), 0.98, math.radians(10.0), math.radians(1.1), math.radians(-44.1), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        
        # Loop until the say method is finished (time t)
        # I check if the time t is finished to stop the motion, really I use 75% of the time t to be sure that the motion is finished before the say method
        while (time.time() - time_ref) < t*0.75:
            self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
        
        # Returning to starting state
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)

    def thinking_gesture(self, t):
        
        # Defining the times of each joint motion 
        times  = [0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        time_ref = time.time()  # reference time to check the time t of the motion

        # Starting position
        angles_start = [math.radians(-24.8), math.radians(-91.4), 0.25, math.radians(95.1), math.radians(9.5), math.radians(10.7), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)
        
        # angles needed for this motion
        angles_t1 = [math.radians(-89.1), math.radians(-57.5), 0.60, math.radians(-34.8), math.radians(4.4), math.radians(-44.1), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        angles_t2 = [math.radians(-89.1), math.radians(-57.5), 0.38, math.radians(-34.8), math.radians(4.4), math.radians(-44.1), math.radians(5.5), math.radians(96.7), 0.69, math.radians(81.6), math.radians(-5.8), math.radians(-1.7)]
        
        # Loop until the say method is finished (time t)
        # I check if the time t is finished to stop the motion, really I use 75% of the time t to be sure that the motion is finished before the say method
        while (time.time() - time_ref) < t*0.75:
            self.motion_service.angleInterpolation(self.joint_names, angles_t1, times, self.isAbsolute)
            self.motion_service.angleInterpolation(self.joint_names, angles_t2, times, self.isAbsolute)
        
        # Returning to starting state
        self.motion_service.angleInterpolation(self.joint_names, angles_start, times, self.isAbsolute)

    def speak_and_move(self, sentence, type_of_motion, t):
        # In this method I have used threads, one for speak and one for moving the robot that enable the code to make run both the say and the motion at the same time in parallel

        # I check if the type_of_motion passed as argument is in the list of admitted gestures
        if type_of_motion in self.admitted_gestures:
            motion_thread = threading.Thread(target= getattr(self, type_of_motion), args=[t]) # create a thread for the motion method (target is the method to run) where fetch the method using the string 'type_of_motion' passed as argument
        
        # The robot always speaks
        tts_thread = threading.Thread(target=self.say, args=(sentence, t))  # create a thread for the say method (target is the method to run)

        tts_thread.start()  # start the thread
        if type_of_motion in self.admitted_gestures:
            motion_thread.start() # continue before the previous line to start also this thread
        
        tts_thread.join()   # wait until the thread to speak is finished
        if type_of_motion in self.admitted_gestures:
            motion_thread.join() #w ait until the thread to move is finished


   


if __name__ == "__main__":
    # Argument Terminal Parser, you need to execute the code using "python Robot.py -ip {your_ip} -port {your_port}"
    parser = argparse.ArgumentParser(description="Robot IP and Port")
    parser.add_argument("-ip", type=str, default='127.0.0.1', help="IP address of the robot (e.g., 127.0.0.1)")
    parser.add_argument("-port", type=int, required=True,  help="Port for communication (e.g., 36439)")

    # Parse the arguments
    args = parser.parse_args()

    robot = Robot(ip=args.ip, port=args.port)
    #robot.hello_gesture_1()   
    #robot.say("Ciao", t=5)
    gesture_list = ['prova','hello_gesture_1', 'hello_gesture_2', 'moving_gesture_single_arm', 'moving_gesture_double_arm', 'thinking_gesture', 'surprise_gesture', 'approval_gesture', 'disapproval_gesture'] 
    for gesture in gesture_list:
        robot.speak_and_move(gesture, type_of_motion=gesture, t=5) 

    #robot.hello_gesture_2()
    #robot.talking_gesture_single_arm()


