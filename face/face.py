from deepface import DeepFace
import sys
import numpy as np
import mediapipe as mp
import cv2
import time


#sys.path.insert(0, './camera') # Add the path to the camera module 


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

'''
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
    #right_eye_x_coords = [coord[0] for coord in right_eye_coords]
    #right_eye_y_coords = [coord[1] for coord in right_eye_coords]
    #left_eye_x_coords = [coord[0] for coord in left_eye_coords]
    #left_eye_y_coords = [coord[1] for coord in left_eye_coords]

    # Compute the left pupil coordinates as the average of the eye landmarks
    left_pupil = (int(face_lm.landmark[468].x * w), int(face_lm.landmark[468].y * h))
    right_pupil = (int(face_lm.landmark[473].x * w), int(face_lm.landmark[473].y * h))
        
    # Compute the center of the left and right eyes
    # The center is computed as the average of the x and y coordinates of the eye landmarks
    #center_right_eye = (sum(right_eye_x_coords) // len(right_eye_x_coords), sum(right_eye_y_coords) // len(right_eye_y_coords))
    #center_left_eye = (sum(left_eye_x_coords) // len(left_eye_x_coords), sum(left_eye_y_coords) // len(left_eye_y_coords))

    outer_boundary_left = (int(face_lm.landmark[33].x * w), int(face_lm.landmark[33].y * h))
    outer_boundary_right = (int(face_lm.landmark[263].x * w), int(face_lm.landmark[263].y * h))

    lower_boundary_left = (int(face_lm.landmark[145].x * w), int(face_lm.landmark[145].y * h))
    lower_boundary_right = (int(face_lm.landmark[374].x * w), int(face_lm.landmark[374].y * h))

    return left_eye_coords, right_eye_coords, left_pupil, right_pupil, outer_boundary_left, outer_boundary_right, lower_boundary_left, lower_boundary_right
'''

def irid_pose_estimator(face_lm, w, h):

    """Estimate the head pose in the given image.
    Args:
        face_lm (list[obj]): the face landmarks obtained from the mediapipe Face Mesh model.
    Outputs:
        
    """
    # Define a list of landmarks used to solve the PnP problem
    # 468-472: left eye irid points
    # 473-477: right eye irid points
    
    landmarks_idx = [468, 469, 470, 471, 472, 473, 474, 475, 476, 477]

    # Create a list of 2D and 3D points for the other landmarks scaling the normalized coordinates to the image dimensions
    irid_2d = [(int(face_lm.landmark[idx].x*w), int(face_lm.landmark[idx].y*h)) for idx in landmarks_idx]
    irid_3d = [(int(face_lm.landmark[idx].x*w), int(face_lm.landmark[idx].y*h), face_lm.landmark[idx].z) for idx in landmarks_idx]

    # Convert the 2D and 3D points to numpy arrays
    irid_2d_np = np.array(irid_2d, dtype=np.float32)
    irid_3d_np = np.array(irid_3d, dtype=np.float32)

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
    success, rot_vec, _ = cv2.solvePnP(irid_3d_np, irid_2d_np, camera_matrix, dist_coeffs)

    if success:
        # Then we trasform the rotation vector to a rotation matrix
        R, _ = cv2.Rodrigues(rot_vec)

        # We extract the Euler angles from the rotation matrix
        # The angles are in radians, we can convert them to degrees if needed
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(R)
        theta_x, theta_y, theta_z = angles[0]*360, angles[1]*360, angles[2]*360

        # Rotation around the x_axis means looking up/down, rotation around the y_axis means looking left/right
        return irid_2d, (theta_x, theta_y, theta_z)
    else:
        print("Head pose estimation failed.")
        return None

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

  

#def gaze_estimator(center_left_eye, left_pupil, center_right_eye, right_pupil, theta):

def gaze_estimator(theta_eye, theta_head):

    """Estimate the gaze direction based on the eye landmarks and pupil coordinates.
    Args:
        theta_eye (tuple): Euler angles of the head pose (theta_x, theta_y, theta_z).
        theta_head (tuple): Euler angles of the head pose (theta_x, theta_y, theta_z).
    Outputs:
        gaze_direction (str): The estimated gaze direction.
    """

    threshold_head_x = 12  # Threshold for horizontal gaze direction of head
    threshold_head_y = 12  # Thresold for vertical gaze direction of head
    #threshold_eye_x = 5  # Threshold for horizontal gaze direction of head
    #threshold_eye_y = 3  # Threshold for vertical gaze direction of head
    
    # Check if the gaze is centered based on the eye and head angles in particular check if the eyes are centered and the head is not turned too much
    if (np.abs(theta_head[0]) > threshold_head_x or np.abs(theta_head[1]) > threshold_head_y):
        return 'not centered' #str(round(np.abs(theta_head[0]), ndigits=1)) + " " + str(round(np.abs(theta_head[1]), ndigits=1))
    # Check if the gaze is centered based on the eye and head angles in particular check if the eyes are turned in the same direction as the head
    #if (theta_eye[0] > epsilon_turn and theta_eye[1] > epsilon_turn and theta_eye[0] > epsilon_turn and theta_eye[1] > epsilon_turn) and ( theta_eye[0] - theta_head[0] > epsilon_turn or theta_eye[1] - theta_head[1] > epsilon_turn):
    #    return "Not Centered2 " + str(theta_eye[0] - theta_head[0]) + " " + str(theta_eye[1] - theta_head[1])
    
    return "centered"

def score(gaze, emotion):
    """Compute a score based on the gaze direction and emotion.
    Args:
        gaze (int): number of frames of centered gaze.
        emotion (str): The emotion with the highest score.
    Outputs:
        score (int): The computed score.
    """
    
    detected_emotion = ''
    wg = 0.5  # Weight for gaze direction
    we = 0.5  # Weight for emotion
    
    if emotion == "happy": #or emotion == "surprise":
        es = 1
        detected_emotion = emotion
    elif emotion == "sad": #or emotion == "angry" or emotion == "disgust" or emotion == "fear":
        es = 0
        detected_emotion = emotion
    elif emotion == "neutral":
        es = 0.5
        detected_emotion = emotion
    else:
        es = 0.5
        
    return gaze * wg + es * we, detected_emotion