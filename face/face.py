from deepface import DeepFace

import sys
sys.path.insert(0, './camera')
from camera import read_camera

import numpy as np
results = DeepFace.analyze(img_path="saved_image.jpg", actions=['emotion'])
d = results[0]['emotion']
print(max(d,key=d.get))
print(results[0]['region'])
