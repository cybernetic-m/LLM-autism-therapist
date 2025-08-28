import sys
sys.path.insert(0, './audio')
sys.path.insert(0, './neo4j_db')
sys.path.insert(0, './llm')
sys.path.insert(0, './face')

import cv2
import mediapipe as mp
import time
import os
from gtts import gTTS

from face_main import analyze_emotion, head_pose_estimator, irid_pose_estimator, gaze_estimator, score, get_screen_resolution
from audio import record_audio
from audio_api import audio_groq_api

def attention_benchmark(q, stop_event):

    # Get the screen resolution
    screen_width, screen_height = get_screen_resolution()
    # Create a named window and move it to the top-right corner of the screen
    window_name = "Engagement Estimation"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, screen_width-50, 0) # Move the window to the top-right corner
    cv2.resizeWindow(window_name, 640, 440) # Resize the window to 640x460

    # Initialize the counter for frames. The emotion will be saved each "num_frames_emotion" frames.
    counter_frames = 0
    counter_frames_ = 0
    num_frames_emotion = 20
    last_save_time = time.time()

    os.makedirs("./benchmark/frames", exist_ok=True)
    
    # Open the default camera (usually the first camera)
    camera = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not camera.isOpened():
        raise("Error: Could not open camera. Check if the camera is connected, or change the idx of the camera in 'camera = cv2.VideoCapture(0)' line.")
        quit()

    # Initialization of gaze score 'g' and engagement score 's', and emotion string
    g = 0
    s = 0
    s_list = []
    detected_emotion = ''

    while not stop_event.is_set():

        #time.sleep(1)  # Sleep for a short time to avoid high CPU usage

        # Read a frame from the camera (ret is a boolean indicating success)
        ret, frame = camera.read()
        counter_frames += 1     # increment the frame counter
        
        if ret is True:
        
            # Save the frame as an image file for DeepFace emotion analysis
            image_path = "image.jpg"
            # Get the image width and height needed for obtaining left eye and right eye landmarks
            h, w, _ = frame.shape
            # Save the frame as an image file
            cv2.imwrite(image_path, frame)

            # Analyze the emotion in the captured frame each "num_frames_emotion_analysis" frames
            if counter_frames % num_frames_emotion == 0:
                emotion = analyze_emotion(image_path)
                s, detected_emotion = score(g/num_frames_emotion, emotion)
                g = 0

            # Initialize the Face Mesh model
            mp_face_mesh = mp.solutions.face_mesh

            # Create a Face Mesh instance with 
            with mp_face_mesh.FaceMesh(max_num_faces=1,     # The maximum number of faces to detect in the image
                                    refine_landmarks=True,   # Enable landmark refinement for eyes and lips (more accurate position of eyes landmarks, needed for gaze estimation)
                                    min_detection_confidence=0.5, # Threshold for face detection confidence: minimum confidence value to detect a face in the image
                                    min_tracking_confidence=0.7  # Threshold for face tracking confidence: minimum confidence value to assume that the face is being tracked correctly between frames
                                    ) as face_mesh:
                
                # Process the image to get face landmarks
                results = face_mesh.process(frame)
                if results.multi_face_landmarks:
                    # Get the first detected face landmarks
                    face_lm = results.multi_face_landmarks[0]
                    # Pass the frame to the eye_landmark_extraction function that returns the left and right eye landmarks, and the pupil coordinates
                    #left_eye_coords, right_eye_coords, left_pupil, right_pupil, outer_boundary_left, outer_boundary_right, lower_boundary_left, lower_boundary_right = eye_landmark_extraction(face_lm, w, h)
                    
                    # Compute the head pose
                    nose_2d, face_2d, theta_head = head_pose_estimator(face_lm, w, h)
                    
                    irid_2d, theta_eye = irid_pose_estimator(face_lm, w, h)
                    #left_eye_coords += irid_2d[0:5]
                    #right_eye_coords += irid_2d[5:]

                    # Gaze estimation
                    gaze = gaze_estimator(theta_eye, theta_head)
                    #print(f"State: {gaze}")
                
                    # Display results
                    if irid_2d:
                        # Draw circles on the eye landmarks
                        #for (x, y) in irid_2d:
                        #    cv2.circle(frame, (x, y), radius=2, color=(255, 0, 0), thickness=-1)
                        #for (x, y) in right_eye_coords[-5:]:
                        #    cv2.circle(frame, (x, y), radius=2, color=(255, 0, 0), thickness=-1)
                        # Draw a red circle at the pupil
                        left_pupil = irid_2d[0]
                        #cv2.circle(frame, irid_2d[0], radius=8, color=(0, 255, 0), thickness=2)
                        #cv2.circle(frame, irid_2d[5], radius=8, color=(0, 255, 0), thickness=2)

                        # Draw the nose landmark and all the landmarks used for head pose estimation
                        cv2.circle(frame, (nose_2d[0], nose_2d[1]), radius=2, color=(0, 0, 255), thickness=-1)  # Draw line from center of left eye to pupil
                        for (x, y) in face_2d:
                            cv2.circle(frame, (x, y), radius=2, color=(0, 0, 255), thickness=-1)
                        
                        '''
                        # Draw lines from the center of the left and right eyes to the pupils
                        cv2.line(frame, outer_boundary_left, left_pupil, (0, 0, 0), 2)  # Draw line from center of left eye to pupil
                        cv2.line(frame, outer_boundary_right, right_pupil, (0, 0, 0), 2)  # Draw line from center of right eye to pupil
                        
                        cv2.line(frame, lower_boundary_left, left_pupil, (0, 0, 0), 2)  # Draw line from center of left eye to pupil
                        cv2.line(frame, lower_boundary_right, right_pupil, (0, 0, 0), 2)  # Draw line from center of right eye to pupil
                        '''
                        p1 = (int(nose_2d[0]), int(nose_2d[1]))
                        p2 = (int(nose_2d[0] + theta_head[1] * 2) , int(nose_2d[1] - theta_head[0] * 2))
                        #p3 = (int(left_pupil[0] + theta_eye[1] * 5) , int(left_pupil[1] - theta_eye[0] * 5))
                
                        cv2.line(frame, p1, p2, (255, 0, 0), 3)
                        #cv2.line(frame, left_pupil, p3, (255, 0, 0), 3)
                        
                        if gaze == 'centered':
                            g += 1
                        
                        # Add the text on the image
                        cv2.putText(frame,str(s) + ' '+ gaze+' '+ detected_emotion, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 2553, 0), 2)

                        # Show the output image
                        cv2.imshow(window_name, frame)
                        current_time = time.time()
                        if current_time - last_save_time  >= 1.0:
                            filename = f"./benchmark/frames/frame_{counter_frames}.jpg"
                            cv2.imwrite(filename, frame)
                            last_save_time = current_time
                            counter_frames_ += 1
                            if counter_frames_ >= 100:
                                stop_event.set()
                                break
                        
                else:
                    pass
                    #print("No landmarks detected.")

            # To stop the loop, press 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    camera.release()
    

def audio_benchmark(samples):
    for i in range(1,samples+1):
        path = "./benchmark/audio/"
        print("recording sample ", i)
        record_audio(path+"audio_sample_"+str(i)+".wav")
        print("transcribing sample ", i)
        response = audio_groq_api(api_key = groq_api_key, model_name = 'whisper-large-v3', audio_path = path+"audio_sample_"+str(i)+".wav")
        with open(path+"transcription_"+str(i)+".txt", "w") as text_file:
            text_file.write(response)
        print("synthesizing sample ", i)
        tts = gTTS(response, lang="it")
        tts.save(path+"tts_"+str(i)+".mp3")
    
    
if __name__ == "__main__":
    import threading
    import queue
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmarking script for attention and audio models.")
    parser.add_argument('-audio_samples', type=int, default=100, help='Number of audio samples to record and transcribe.')
    parser.add_argument('-audio', action='store_true', help='Flag to run audio benchmark.')
    parser.add_argument('-attention', action='store_true', help='Flag to run attention benchmark.')
    args = parser.parse_args()
    
    with open("llm/api_key.txt", "r") as file:
        groq_api_key = file.read()
    
    if args.audio:
        os.makedirs("./benchmark/audio/", exist_ok=True)
        audio_benchmark(args.audio_samples)
        
    if args.attention:
        stop_event = threading.Event()
        # Create a queue for the results of the thread execution
        q = queue.Queue()
        # Create the face thread
        thread_face = threading.Thread(target=attention_benchmark, args=(q,stop_event))
        
        thread_face.start()