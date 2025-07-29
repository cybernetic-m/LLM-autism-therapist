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


def eye_landmark_extraction(face_lm, w, h):

    """Estimate the gaze direction in the given image.
    Args:
        face_lm (list[obj]): the face landmarks obtained from the mediapipe Face Mesh model.
    Outputs:
        left_eye_coords (list): List of coordinates of the left eye landmarks.
        right_eye_coords (list): List of coordinates of the right eye landmarks.
        left_pupil (tuple): Coordinates of the left pupil.
        right_pupil (tuple): Coordinates of the right pupil.
        center_left_eye (tuple): Coordinates of the center of the left eye.
        center_right_eye (tuple): Coordinates of the center of the right eye.
    """

    # Initialize the lists of mediapipe landmarks that are utils for the extraction
    right_eye_landmarks = [263, 362, 387, 386, 385, 373, 374, 380, 381, 382]
    left_eye_landmarks = [33, 133, 160, 159, 158, 144, 145, 153, 154, 155]

    # To extract the coordinates of the left and right eye landmarks, we need to scale the normalized coordinates to the image dimensions
    # because the landmarks are normalized to the range [0, 1] relative to the image size.
    # Ex. if the image is 640x480, the x coordinate of a landmark with normalized x=0.5 will be 320 (0.5 * 640)
    
    # Extract the landmarks for the left eye
    left_eye_coords = [(int(face_lm.landmark[idx].x * w), int(face_lm.landmark[idx].y * h)) for idx in left_eye_landmarks]
    
    # Extract the landmarks for the right eye
    right_eye_coords = [(int(face_lm.landmark[idx].x * w), int(face_lm.landmark[idx].y * h)) for idx in right_eye_landmarks]

    # Compute the pupil coords left and right eye
    # Create lists of x and y coordinates for the left and right eye landmarks
    right_eye_x_coords = [coord[0] for coord in right_eye_coords]
    right_eye_y_coords = [coord[1] for coord in right_eye_coords]
    left_eye_x_coords = [coord[0] for coord in left_eye_coords]
    left_eye_y_coords = [coord[1] for coord in left_eye_coords]

    # Compute the left pupil coordinates as the average of the eye landmarks
    left_pupil = (int(face_lm.landmark[468].x * w), int(face_lm.landmark[468].y * h))
    right_pupil = (int(face_lm.landmark[473].x * w), int(face_lm.landmark[473].y * h))
        
    # Compute the center of the left and right eyes
    # The center is computed as the average of the x and y coordinates of the eye landmarks
    center_right_eye = (sum(right_eye_x_coords) // len(right_eye_x_coords), sum(right_eye_y_coords) // len(right_eye_y_coords))
    center_left_eye = (sum(left_eye_x_coords) // len(left_eye_x_coords), sum(left_eye_y_coords) // len(left_eye_y_coords))

    return left_eye_coords, right_eye_coords, left_pupil, right_pupil, center_left_eye, center_right_eye



def head_pose_estimator(face_lm, w, h):

    """Estimate the head pose in the given image.
    Args:
        face_lm (list[obj]): the face landmarks obtained from the mediapipe Face Mesh model.
    Outputs:
        
    """
    # Define a list of landmarks used to solve the PnP problem
    # 1: Nose tip
    # 33: Left eye outer corner
    # 263: Right eye outer corner
    # 61: Left mouth corner
    # 291: Right mouth corner
    # 199: Chin
    landmarks_idx = [1, 33, 263, 61, 291, 199]

    # Create a tuple of the nose landmark coordinates in 2D pixels scaling the normalized coordinates to the image dimensions
    nose_2d = (int(face_lm.landmark[1].x * w), int(face_lm.landmark[1].y * h))

    # Create a list of 2D and 3D points for the other landmarks scaling the normalized coordinates to the image dimensions
    face_2d = [(int(face_lm.landmark[idx].x*w), int(face_lm.landmark[idx].y*h)) for idx in landmarks_idx]
    face_3d = [(int(face_lm.landmark[idx].x*w), int(face_lm.landmark[idx].y*h), face_lm.landmark[idx].z) for idx in landmarks_idx]

    # Convert the 2D and 3D points to numpy arrays
    face_2d_np = np.array(face_2d, dtype=np.float32)
    face_3d_np = np.array(face_3d, dtype=np.float32)

    # Define the camera matrix (assuming a simple pinhole camera model), focal length and distortion coefficients
    cx, cy = w / 2, h / 2  # Principal point (center of the image)
    f = 1.0*w  # Focal length (assume the focal length is equal to the width of the image as usual)
    camera_matrix = np.array([[f, 0, cx],
                              [0, f, cy],
                              [0, 0, 1]])
    dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion

    # We apply the solvePnP function to estimate the rotation vector
    # success is a boolean indicating if the function was successful
    # rot_vec is the rotation vector that describes the rotation of the head: ex. (theta_x, theta_y, theta_z) are the angles of rotation around the x, y, and z axes
    success, rot_vec, _ = cv2.solvePnP(face_3d_np, face_2d_np, camera_matrix, dist_coeffs)

    if success:
        # Then we trasform the rotation vector to a rotation matrix
        R, _ = cv2.Rodrigues(rot_vec)

        # We extract the Euler angles from the rotation matrix
        # The angles are in radians, we can convert them to degrees if needed
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(R)
        theta_x, theta_y, theta_z = angles[0]*360, angles[1]*360, angles[2]*360

        # Rotation around the x_axis means looking up/down, rotation around the y_axis means looking left/right
        return nose_2d, face_2d, (theta_x, theta_y, theta_z)
    else:
        print("Head pose estimation failed.")
        return None

  

def gaze_estimator(center_left_eye, left_pupil, center_right_eye, right_pupil, theta):
    
    """Estimate the gaze direction based on the eye landmarks and pupil coordinates.
    Args:
        center_left_eye (tuple): Coordinates of the center of the left eye.
        left_pupil (tuple): Coordinates of the left pupil.
        center_right_eye (tuple): Coordinates of the center of the right eye.
        right_pupil (tuple): Coordinates of the right pupil.
        theta (tuple): Euler angles of the head pose (theta_x, theta_y, theta_z).
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
    threshold_theta_x = 10  # Threshold for head pose rotation around the x-axis (looking up/down)
    threshold_theta_y = 10  # Threshold for head pose rotation around the y-axis (looking left/right)
    
    

    if ((sum_x < threshold_x and sum_y < threshold_y) and (abs(theta[0]) < threshold_theta_x and abs(theta[1]) < threshold_theta_y)) or (sum_x > threshold_x and abs(theta[0]) > threshold_theta_x) or (sum_y > threshold_y and abs(theta[0]) > threshold_theta_y) :
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
            emotion_dict[emotion] += 1

        # Extract landmarks from the captured frame and extract gaze direction
        # Firstly convert the image to RGB using cv2.cvtColor
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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
                left_eye_coords, right_eye_coords, left_pupil, right_pupil, center_left_eye, center_right_eye = eye_landmark_extraction(face_lm, w, h)
                
                # Compute the head pose
                nose_2d, face_2d, theta = head_pose_estimator(face_lm, w, h)

                # Gaze estimation
                gaze = gaze_estimator(center_left_eye, left_pupil, center_right_eye, right_pupil, theta)
                print(f"State: {gaze}")
            
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

                    # Draw the nose landmark and all the landmarks used for head pose estimation
                    cv2.circle(frame, (nose_2d[0], nose_2d[1]), radius=2, color=(0, 0, 255), thickness=-1)  # Draw line from center of left eye to pupil
                    for (x, y) in face_2d:
                        cv2.circle(frame, (x, y), radius=2, color=(0, 0, 255), thickness=-1)
                    
                    # Draw lines from the center of the left and right eyes to the pupils
                    cv2.line(frame, center_left_eye, left_pupil, (0, 0, 0), 2)  # Draw line from center of left eye to pupil
                    cv2.line(frame, center_right_eye, right_pupil, (0, 0, 0), 2)  # Draw line from center of right eye to pupil
                    
                    p1 = (int(nose_2d[0]), int(nose_2d[1]))
                    p2 = (int(nose_2d[0] + theta[1] * 5) , int(nose_2d[1] - theta[0] * 5))
            
                    cv2.line(frame, p1, p2, (255, 0, 0), 3)

                    # Add the text on the image
                    cv2.putText(frame, gaze, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

                    # Show the output image
                    cv2.imshow("Gaze Estimation", frame)
            else:
                print("No landmarks detected.")

        # To stop the loop, press 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

camera.release()
    



