import re

with open('inference.py', 'r') as f:
    code = f.read()

gd_new = """def process_grounding_dino(image_path: str, prompt: str, box_threshold: float = 0.35, text_threshold: float = 0.25):
    \"\"\"
    Run Grounding DINO to detect objects based on text prompt.
    Returns list of dicts with bbox (percentages) and confidence.
    \"\"\"
    model = get_gd_model()
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    
    # Grounding DINO predict
    detections, phrases = model.predict_with_caption(
        image=image,
        caption=prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold
    )
    
    results = []
    colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
    
    for i, (xyxy, confidence, phrase) in enumerate(zip(detections.xyxy, detections.confidence, phrases)):
        x_min, y_min, x_max, y_max = xyxy
        
        # Convert to Top-Left x, y, width, height in percentages for frontend overlay
        x_pct = (x_min / width) * 100
        y_pct = (y_min / height) * 100
        w_pct = ((x_max - x_min) / width) * 100
        h_pct = ((y_max - y_min) / height) * 100
        
        results.append({
            "id": f"gd_{i}",
            "label": phrase,
            "confidence": float(confidence),
            "bbox": {"x": float(x_pct), "y": float(y_pct), "width": float(w_pct), "height": float(h_pct)},
            "color": colors[i % len(colors)]
        })
        
    return results"""

sam_new = """def process_sam(image_path: str, prompt: str, box_threshold: float = 0.35, text_threshold: float = 0.25):
    \"\"\"
    Run Grounding DINO to get bbox, then SAM to generate mask.
    Returns list of dicts with bbox, mask, and confidence.
    \"\"\"
    # 1. Get bbox from GD
    model = get_gd_model()
    image_bgr = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    height, width, _ = image_rgb.shape
    
    detections, phrases = model.predict_with_caption(
        image=image_bgr,
        caption=prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold
    )
    
    if len(detections.xyxy) == 0:
        return []
        
    # 2. Get masks from SAM
    predictor = get_sam_predictor()
    predictor.set_image(image_rgb)
    
    results = []
    colors = ['#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#eab308']
    
    for i, (xyxy, confidence, phrase) in enumerate(zip(detections.xyxy, detections.confidence, phrases)):
        input_box = xyxy
        
        masks, _, _ = predictor.predict(
            point_coords=None,
            point_labels=None,
            box=input_box,
            multimask_output=False,
        )
        
        mask = masks[0] # Single mask output
        
        # Convert mask to polygon (contours)
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        segment_points_pct = ""
        if len(contours) > 0:
            # Take the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            # Simplify polygon slightly
            epsilon = 0.005 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
            
            # Convert to percentages for CSS polygon: "x,y x,y x,y"
            points = []
            for point in approx:
                px = (point[0][0] / width) * 100
                py = (point[0][1] / height) * 100
                points.append(f"{px},{py}")
            segment_points_pct = " ".join(points)
            
        x_min, y_min, x_max, y_max = xyxy
        x_pct = (x_min / width) * 100
        y_pct = (y_min / height) * 100
        w_pct = ((x_max - x_min) / width) * 100
        h_pct = ((y_max - y_min) / height) * 100
        
        results.append({
            "id": f"sam_{i}",
            "label": f"{phrase} (Segmented)",
            "confidence": float(confidence),
            "bbox": {"x": float(x_pct), "y": float(y_pct), "width": float(w_pct), "height": float(h_pct)},
            "segment": segment_points_pct,
            "color": colors[i % len(colors)]
        })
        
    return results"""

code = re.sub(r"def process_grounding_dino.*?(?=def process_sam)", gd_new + "\n\n", code, flags=re.DOTALL)
code = re.sub(r"def process_sam.*", sam_new + "\n", code, flags=re.DOTALL)

with open('inference.py', 'w') as f:
    f.write(code)
