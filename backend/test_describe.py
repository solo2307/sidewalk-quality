import sys
import os
sys.path.append('.')
from inference import describe_area

def test_describe():
    test_img = "backend/temp/test_road.jpg"
    if not os.path.exists(test_img):
        print(f"No test image found at {test_img}.")
        return

    bbox = {"x": 20, "y": 40, "width": 60, "height": 40}
    
    print(f"Testing description for 'road' using {test_img}...")
    res = describe_area(test_img, bbox, "road")
    print("Result:", res)

if __name__ == "__main__":
    test_describe()
