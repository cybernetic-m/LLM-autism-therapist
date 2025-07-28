from deepface import DeepFace
import sys
import numpy as np
import mediapipe as mp
import cv2
import time


sys.path.insert(0, './camera') # Add the path to the camera module 


def analyze_emotion(image_path):
    """Analyze the emotion in the given image (one frame of the video) using DeepFace.
    Args:
        image_path (str): Path to the image file.
    Outputs:
        emotion (str): The emotion with the highest score.
    """

    results = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=False)
    d = results[0]['emotion']
    emotion = max(d,key=d.get)
    return emotion


def eye_landmark_extraction(image):

    """Estimate the gaze direction in the given image.
    Args:
        image_path (str): Path to the image file.
    Outputs:
        
    """

    # Initialize the Face Mesh model
    mp_face_mesh = mp.solutions.face_mesh

    # Get the image width and height needed for obtaining left eye and right eye landmarks
    h, w, _ = image.shape

    # Initialize the lists of left and right eye landmarks
    left_eye_landmarks = [33, 133, 160, 159, 158, 144, 145, 153, 154, 155]
    right_eye_landmarks = [263, 362, 387, 386, 385, 373, 374, 380, 381, 382]

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
            face = results.multi_face_landmarks[0]  # Get the first detected face landmarks
            
            # To extract the coordinates of the left and right eye landmarks, we need to scale the normalized coordinates to the image dimensions
            # because the landmarks are normalized to the range [0, 1] relative to the image size.
            # Ex. if the image is 640x480, the x coordinate of a landmark with normalized x=0.5 will be 320 (0.5 * 640)
            
            # Extract the landmarks for the left eye
            left_eye_coords = [(int(face.landmark[idx].x * w), int(face.landmark[idx].y * h)) for idx in left_eye_landmarks]
            
            # Extract the landmarks for the right eye
            right_eye_coords = [(int(face.landmark[idx].x * w), int(face.landmark[idx].y * h)) for idx in right_eye_landmarks]

            # Compute the pupil coords left and right eye
            # Create lists of x and y coordinates for the left and right eye landmarks
            right_eye_x_coords = [coord[0] for coord in right_eye_coords]
            right_eye_y_coords = [coord[1] for coord in right_eye_coords]
            left_eye_x_coords = [coord[0] for coord in left_eye_coords]
            left_eye_y_coords = [coord[1] for coord in left_eye_coords]

            # Compute the left pupil coordinates as the average of the eye landmarks
            left_pupil = (int(face.landmark[468].x * w), int(face.landmark[468].y * h))
            right_pupil = (int(face.landmark[473].x * w), int(face.landmark[473].y * h))
             
            # Compute the center of the left and right eyes
            # The center is computed as the average of the x and y coordinates of the eye landmarks
            center_right_eye = (sum(right_eye_x_coords) // len(right_eye_x_coords), sum(right_eye_y_coords) // len(right_eye_y_coords))
            center_left_eye = (sum(left_eye_x_coords) // len(left_eye_x_coords), sum(left_eye_y_coords) // len(left_eye_y_coords))

            return left_eye_coords, right_eye_coords, left_pupil, right_pupil, center_left_eye, center_right_eye
        else:
            print(f"No face detected")
            return None, None, None, None, None, None
        

def gaze_estimator(center_left_eye, left_pupil, center_right_eye, right_pupil):
    
    """Estimate the gaze direction based on the eye landmarks and pupil coordinates.
    Args:
        center_left_eye (tuple): Coordinates of the center of the left eye.
        left_pupil (tuple): Coordinates of the left pupil.
        center_right_eye (tuple): Coordinates of the center of the right eye.
        right_pupil (tuple): Coordinates of the right pupil.
    Outputs:
        gaze_direction (str): The estimated gaze direction.
    """

    # Calculate the distance between the centers of the left and right eyes
    dist_right_x = center_right_eye[0] - right_pupil[0]
    dist_right_y = center_right_eye[1] - right_pupil[1]
    dist_left_x = center_left_eye[0] - left_pupil[0]
    dist_left_y = center_left_eye[1] - left_pupil[1]

    # Compute the sum of the absolute distances in x and y directions
    sum_x = np.abs(dist_right_x + dist_left_x)
    sum_y = np.abs(dist_right_y + dist_left_y)

    # Having a threshold for the x, and one for the y direction
    threshold_x = 15  # Threshold for x direction (looking left/right)distracted
    threshold_y = 6  # Threshold for y direction (looking up/down)

    if sum_x < threshold_x and sum_y < threshold_y:
        return "Centered"  # Gaze is centered
    else:
        return "Not Centered"  # Gaze is not centered
    


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

# Drawing utils of mediapipe for drawing landmarks on the image
mp_drawing = mp.solutions.drawing_utils

# Check if the camera opened successfully
if not camera.isOpened():
    raise("Error: Could not open camera. Check if the camera is connected, or change the idx of the camera in 'camera = cv2.VideoCapture(0)' line.")
    quit()


while True:

    time.sleep(1)  # Sleep for a short time to avoid high CPU usage

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

        # Extract landmarks from the captured frame and extract gaze direction
        # Firstly convert the image to RGB using cv2.cvtColor
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Pass the frame to the eye_landmark_extraction function that returns the left and right eye landmarks, and the pupil coordinates
        left_eye_coords, right_eye_coords, left_pupil, right_pupil, center_left_eye, center_right_eye = eye_landmark_extraction(frame)
        
        # Display results
        if left_eye_coords and right_eye_coords:
            # Draw circles on the eye landmarks
            for (x, y) in left_eye_coords:
                cv2.circle(frame, (x, y), radius=2, color=(255, 0, 0), thickness=-1)
            for (x, y) in right_eye_coords:
                cv2.circle(frame, (x, y), radius=2, color=(255, 0, 0), thickness=-1)
            # Draw a red circle at the pupil
            cv2.circle(frame, (left_pupil[0], left_pupil[1]), radius=8, color=(0, 255, 0), thickness=2)
            cv2.circle(frame, (right_pupil[0], right_pupil[1]), radius=8, color=(0, 255, 0), thickness=2)

            # Draw the center of the left and right eyes
            cv2.circle(frame, (center_left_eye[0], center_left_eye[1]), radius=2, color=(0, 0, 255), thickness=-1)  # Draw line from center of left eye to pupil
            cv2.circle(frame, (center_right_eye[0], center_right_eye[1]), radius=2, color=(0, 0, 255), thickness=-1)  # Draw line from center of left eye to pupil
            
            # Draw lines from the center of the left and right eyes to the pupils
            cv2.line(frame, center_left_eye, left_pupil, (0, 0, 0), 2)  # Draw line from center of left eye to pupil
            cv2.line(frame, center_right_eye, right_pupil, (0, 0, 0), 2)  # Draw line from center of right eye to pupil

            # Gaze estimation
            gaze = gaze_estimator(center_left_eye, left_pupil, center_right_eye, right_pupil)
            print(f"State: {gaze}")
            
            # Show the output image
            cv2.imshow("Eye Landmarks", frame)
        else:
            print("No landmarks detected.")

        # To stop the loop, press 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

camera.release()
    



