import sys, numpy as np, cv2
sys.path.append('.')
from inference import get_gd_model
print("Testing GD Direct...")
model = get_gd_model()
img = np.zeros((100, 100, 3), dtype=np.uint8)
res = model.predict_with_classes(image=img, classes=['test'], box_threshold=0.35, text_threshold=0.25)
print("Type of result:", type(res))
if isinstance(res, tuple):
    print("Len of tuple:", len(res))
else:
    print("Attrs:", dir(res))
