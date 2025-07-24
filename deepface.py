from deepface import DeepFace
import numpy as np
results = DeepFace.analyze(img_path="image2.jpg", actions=['emotion'])
d = results[0]['emotion']
print(max(d,key=d.get))
print(results[0]['region'])
