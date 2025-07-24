from deepface import DeepFace
import sys
sys.path.insert(0, './camera')
import numpy as np
import mediapipe as mp
import gaze
import cv2


def analyze_emotion(image_path):
    """Analyze the emotion in the given image (one frame of the video) using DeepFace.
    Args:
        image_path (str): Path to the image file.
    Outputs:
        emotion (str): The emotion with the highest score.
    """

    results = DeepFace.analyze(img_path=image_path, actions=['emotion'])
    d = results[0]['emotion']
    emotion = max(d,key=d.get)
    return emotion


def landmark_extraction(image):
    """Estimate the gaze direction in the given image.
    Args:
        image_path (str): Path to the image file.
    Outputs:
        gaze (str): The estimated gaze direction.
    """

    # Initialize the Face Mesh model
    mp_face_mesh = mp.solutions.face_mesh

    # Create a Face Mesh instance with 
    with mp_face_mesh.FaceMesh(max_num_faces=1,     # The maximum number of faces to detect in the image
                               refine_landmarks=True,   # Enable landmark refinement for eyes and lips (more accurate position of eyes landmarks, needed for gaze estimation)
                               min_detection_confidence=0.5, # Threshold for face detection confidence: minimum confidence value to detect a face in the image
                               min_tracking_confidence=0.7  # Threshold for face tracking confidence: minimum confidence value to assume that the face is being tracked correctly between frames
                               ) as face_mesh:

        # Process the image to get face landmarks
        results = face_mesh.process(image)

        # Return None if no face landmarks are detected, or return the first detected face landmarks
        if results.multi_face_landmarks:
            return results.multi_face_landmarks
        else:
            return None


# Initialize the counter for frames. The emotion will be saved each "num_frames_emotion" frames.
counter_frames = 0
num_frames_emotion = 20

# Initialize a dictionary to store emotion counts during simulation
emotion_dict = {
    'angry': 0,
    'disgust': 0,
    'fear': 0,
    'happy': 0,
    'sad': 0,
    'surprise': 0,
    'neutral': 0
}

# Open the default camera (usually the first camera)
camera = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not camera.isOpened():
    raise("Error: Could not open camera. Check if the camera is connected, or change the idx of the camera in 'camera = cv2.VideoCapture(0)' line.")
    quit()

while True:

    # Read a frame from the camera (ret is a boolean indicating success)
    ret, frame = camera.read()
    counter_frames += 1     # increment the frame counter
    
    if ret is True:
     
        # Save the frame as an image file for DeepFace emotion analysis
        image_path = "image.jpg"
        cv2.imwrite(image_path, frame)

        # Analyze the emotion in the captured frame each "num_frames_emotion_analysis" frames
        if counter_frames % num_frames_emotion == 0:
            emotion = analyze_emotion(image_path)
            emotion_dict[emotion] += 1

        # Extract landmarks from the captured frame
        landmarks = landmark_extraction(frame)
        # Estimate the gaze direction in the captured frame
        # TODO

        # If the "Esc" button is pressed for 2 ms, it exits the loop
        if cv2.waitKey(2) & 0xFF == 27:          
            break

camera.release()
    



