import sys
sys.path.append('.')
from inference import process_grounding_dino, process_sam
try:
    print("Testing GD...")
    gd_res = process_grounding_dino('uploads/dummy.jpg', 'test')
    print("GD OK:", gd_res)
except Exception as e:
    print("GD Error:", e)

try:
    print("Testing SAM...")
    sam_res = process_sam('uploads/dummy.jpg', 'test')
    print("SAM OK:", sam_res)
except Exception as e:
    print("SAM Error:", e)
