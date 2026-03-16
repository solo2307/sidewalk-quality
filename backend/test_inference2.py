import sys
import numpy as np
import cv2
sys.path.append('.')
from inference import get_gd_model

try:
    print("Testing GD Direct...")
    model = get_gd_model()
    # Create valid numpy image RGB
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    boxes, logits, phrases = model.predict(image=img, caption='test', box_threshold=0.35, text_threshold=0.25)
    print("Direct Predict OK! Boxes:", len(boxes))
except Exception as e:
    print("Direct Predict Error:", e)
