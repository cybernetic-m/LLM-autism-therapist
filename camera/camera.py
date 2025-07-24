import cv2

def read_camera():

    # Open the default camera (usually the first camera)
    camera = cv2.VideoCapture(0)
    
    # Check if the camera opened successfully
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return None
    
    # Read a frame from the camera (ret is a boolean indicating success)
    ret, frame = camera.read()

    if not ret:
        print("Error: Could not read frame from camera.")
        camera.release()
        return None
    else:
        # Release the camera after reading the frame
        camera.release()
        return frame
    

frame = read_camera()
    
if frame is not None:
    # Display the captured frame
    cv2.imshow('Camera Frame', frame)
    file_name = "saved_image.jpg"
    cv2.imwrite(file_name, frame)
    print(f"Image saved as {file_name}")
        
       