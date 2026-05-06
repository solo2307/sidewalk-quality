import os
import torch
import numpy as np
from PIL import Image
import cv2
import time

# Import Grounding DINO
from groundingdino.util.inference import Model as GroundingDINOModel
from segment_anything import sam_model_registry, SamPredictor

# Check device
device = 'cpu'
if os.environ.get('FORCE_CPU') == '1':
    device = 'cpu'
elif torch.cuda.is_available():
    device = 'cuda'
elif torch.backends.mps.is_available():
    device = 'mps'
print(f"Using device: {device}")

import glob

# Paths
WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weights")

# Dynamically find the config in the venv site-packages
venv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv")
config_matches = glob.glob(os.path.join(venv_path, "lib", "python3.*", "site-packages", "groundingdino", "config", "GroundingDINO_SwinT_OGC.py"))
GD_CONFIG = config_matches[0] if config_matches else "GroundingDINO_SwinT_OGC.py" # fallback

GD_WEIGHTS = os.path.join(WEIGHTS_DIR, "groundingdino_swint_ogc.pth")
SAM_WEIGHTS = os.path.join(WEIGHTS_DIR, "sam_vit_b_01ec64.pth")
SAM_TYPE = "vit_b"

# Lazy load models to save memory during startup until first request
_gd_model = None
_sam_predictor = None
_internvl_model = None

INTERNVL_WEIGHTS = os.path.join(WEIGHTS_DIR, "OpenGVLab_InternVL3_5-8B-Q4_K_M.gguf")
INTERNVL_PROJ = os.path.join(WEIGHTS_DIR, "mmproj-OpenGVLab_InternVL3_5-8B-f16.gguf")

def get_gd_model():
    global _gd_model
    if _gd_model is None:
        print(f"Loading Grounding DINO on {device}...")
        start_time = time.time()
        try:
            _gd_model = GroundingDINOModel(model_config_path=GD_CONFIG, model_checkpoint_path=GD_WEIGHTS, device=device)
            print(f"Grounding DINO loaded in {time.time() - start_time:.2f}s")
        except Exception as e:
            # Fallback for config
            print(f"Failed standard load, trying to download config: {e}")
            import urllib.request
            fallback_config = os.path.join(os.path.dirname(__file__), "GroundingDINO_SwinT_OGC.py")
            if not os.path.exists(fallback_config):
                url = "https://raw.githubusercontent.com/IDEA-Research/GroundingDINO/main/groundingdino/config/GroundingDINO_SwinT_OGC.py"
                urllib.request.urlretrieve(url, fallback_config)
            _gd_model = GroundingDINOModel(model_config_path=fallback_config, model_checkpoint_path=GD_WEIGHTS, device=device)
    return _gd_model

def get_sam_predictor():
    global _sam_predictor
    if _sam_predictor is None:
        print(f"Loading SAM on {device}...")
        start_time = time.time()
        # SAM model needs to be carefully moved to device
        try:
            sam = sam_model_registry[SAM_TYPE](checkpoint=SAM_WEIGHTS)
            sam.to(device=device)
            _sam_predictor = SamPredictor(sam)
            print(f"SAM loaded in {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"Failed to load SAM on {device}, trying CPU. Error: {e}")
            sam = sam_model_registry[SAM_TYPE](checkpoint=SAM_WEIGHTS)
            sam.to(device='cpu')
            _sam_predictor = SamPredictor(sam)
    return _sam_predictor

def get_internvl_model():
    global _internvl_model
    if _internvl_model is None:
        print("Loading InternVL...")
        try:
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import Llava15ChatHandler
            
            chat_handler = Llava15ChatHandler(clip_model_path=INTERNVL_PROJ)
            _internvl_model = Llama(
                model_path=INTERNVL_WEIGHTS,
                chat_handler=chat_handler,
                n_ctx=2048, # Sufficient for description
                n_gpu_layers=-1 if device != 'cpu' else 0,
                verbose=True # Enabled for verification of Metal/MPS usage
            )
        except Exception as e:
            print(f"Failed to load InternVL: {e}")
            _internvl_model = False # Mark as failed
    return _internvl_model

def process_grounding_dino(image_path: str, prompt: str, box_threshold: float = 0.35, text_threshold: float = 0.25):
    """
    Run Grounding DINO to detect objects based on text prompt.
    Returns list of dicts with bbox (percentages) and confidence.
    """
    model = get_gd_model()
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image at {image_path}")
        
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
        
    return results

def process_sam(image_path: str, prompt: str, box_threshold: float = 0.35, text_threshold: float = 0.25):
    """
    Run Grounding DINO to get bbox, then SAM to generate mask.
    Returns list of dicts with bbox, mask, and confidence.
    """
    # 1. Get bbox from GD
    model = get_gd_model()
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError(f"Could not load image at {image_path}")
        
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
        
        # Ensure mask is placed on the exact same device if using MPS. We can pass a tensor.
        import torch
        input_box_tensor = torch.tensor(input_box, device=predictor.device)
        
        masks, _, _ = predictor.predict(
            point_coords=None,
            point_labels=None,
            box=input_box_tensor.cpu().numpy(),  # predictor.predict expects numpy arrays
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
        
    return results

def describe_area(image_path: str, bbox_pct: dict, feature_label: str = "object"):
    """
    Crop the image based on percentage-based bbox and describe it using InternVL.
    Enforces OSM-like material and smoothness tags.
    """
    model = get_internvl_model()
    if not model:
        return "InternVL model not available."
        
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    
    # Convert percentages to pixel coordinates
    left = (bbox_pct['x'] / 100) * width
    top = (bbox_pct['y'] / 100) * height
    right = ((bbox_pct['x'] + bbox_pct['width']) / 100) * width
    bottom = ((bbox_pct['y'] + bbox_pct['height']) / 100) * height
    
    # Add a bit of padding (15%) for better context
    padding_w = (right - left) * 0.15
    padding_h = (bottom - top) * 0.15
    left = max(0, left - padding_w)
    top = max(0, top - padding_h)
    right = min(width, right + padding_w)
    bottom = min(height, bottom + padding_h)
    
    crop = image.crop((left, top, right, bottom))
    
    import base64
    from io import BytesIO
    
    buffered = BytesIO()
    crop.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{img_base64}"
    
    print(f"Describing {feature_label} with InternVL using strict JSON OSM tagging...")
    # Define tag sets
    surface_materials = "asphalt, concrete, concrete_plates, paving_stones, paving_slabs, sett, cobblestone, unhewn_cobblestone, bricks, stone, gravel, fine_gravel, compacted, dirt, ground, grass, sand, mud, wood, metal"
    structural_materials = "brick, brickwork, concrete, reinforced_concrete, stone, sandstone, limestone, granite, wood, timber_framing, steel, glass, metal, plaster, adobe, mud, clay, rammed_earth, prefab, block, tile, roof_tiles, shingle, bitumen, asphalt, slate, thatch, eternit, solar_panels, other"
    smoothness_tags = "excellent, good, intermediate, bad, very_bad, horrible, very_horrible, impassable, not_visible"
    smoothness_definitions = """
       Use the OpenStreetMap smoothness scale for the visible sidewalk or path surface:

           excellent: new or nearly perfect surface, very regular and flat.
           good: mostly smooth, with only minor wear or narrow cracks.
           intermediate: usable but visibly imperfect, with patches, joints, shallow cracks, or mild unevenness.
           bad: damaged or uncomfortable surface, with many cracks, bumps, potholes, or uneven areas.
           very_bad: very rough or strongly uneven surface, difficult for wheelchairs, strollers, or small wheels.
           horrible: extremely rough surface, passable only with difficulty.
           very_horrible: severe obstacles, rubble, deep ruts, or broken surface; barely passable.
           impassable: not usable as a sidewalk or path.
           not_visible: the sidewalk/path surface is not visible enough to judge.
       """
    OSM_TO_SCORE = {
        "excellent": 5,
        "good": 5,
        "intermediate": 4,
        "bad": 3,
        "very_bad": 2,
        "horrible": 2,
        "very_horrible": 1,
        "impassable": 1,
        "not_visible": None,
    }
    # # Define tag sets
    # surface_materials = "asphalt, concrete, concrete_plates, paving_stones, paving_slabs, sett, cobblestone, unhewn_cobblestone, bricks, stone, gravel, fine_gravel, compacted, dirt, ground, grass, sand, mud, wood, metal"
    # structural_materials = "brick, brickwork, concrete, reinforced_concrete, stone, sandstone, limestone, granite, wood, timber_framing, steel, glass, metal, plaster, adobe, mud, clay, rammed_earth, prefab, block, tile, roof_tiles, shingle, bitumen, asphalt, slate, thatch, eternit, solar_panels, other"
    # smoothness_tags = "excellent, good, intermediate, bad, very_bad, horrible, very_horrible, impassable"
    
    # Select schema and materials based on Categories
    label_lower = feature_label.lower()
    is_building = any(w in label_lower for w in ["building", "house", "structure", "wall", "fence", "garage", "shed", "facade", "apartment", "villa", "cottage", "construction", "home", "tower", "block", "hut", "barn", "cabin"])
    is_roof = any(w in label_lower for w in ["roof", "rooftop"])
    is_road_like = any(w in label_lower for w in ["road", "sidewalk", "path", "street", "track", "pavement", "way", "highway", "asphalt", "concrete", "lane", "driveway", "route", "trail"])
    
    category = "other"
    if is_roof:
        category = "roof"
        allowed_materials = structural_materials
        schema = {
            "feature": feature_label,
            "material": "<one value from list>",
            "flat": "yes | no"
        }
    elif is_building:
        category = "building"
        allowed_materials = structural_materials
        schema = {
            "feature": feature_label,
            "material": "<one value from list>",
            "purpose": "residential | commercial | public | others",
            "floors": "integer_or_null"
        }
    elif is_road_like:
        category = "road/surface"
        allowed_materials = surface_materials
        schema = {
            "feature": feature_label,
            "surface": "<one value from allowed surface list>",
            "smoothness_osm": "<excellent | good | intermediate | bad | very_bad | horrible | very_horrible | impassable | not_visible>",
            "smoothness_score_1_to_5": "<integer 1-5 or null>",
            "confidence": "<low | medium | high>",
            "visible_evidence": "<short reason based only on visible surface condition>"
        }
    else:
        # Default for other categories
        category = "other"
        schema = {
            "feature": feature_label,
            "description": "A very short, 1-sentence analysis of this object's condition or type."
        }
        allowed_materials = "N/A"

    print(f"Object: '{feature_label}' classified as: {category}")

    import json
    schema_str = json.dumps(schema, indent=2)

    system_msg = (
        "Return ONLY a valid JSON object. No conversation. No markdown code blocks.\n"
        f"Exact JSON schema to follow:\n{schema_str}\n\n"
        f"Allowed materials/surfaces, if applicable:\n{allowed_materials}\n\n"
        f"Allowed OSM smoothness values, if applicable:\n{smoothness_tags}\n\n"
        f"{smoothness_definitions}\n\n"
        "Allowed purpose: residential, commercial, public, others.\n"
        "For 'flat', use only 'yes' or 'no'.\n"
        "Judge only the visible cropped region.\n"
        "For sidewalks, paths, pavements, roads, or walkways, base smoothness only on visible surface regularity, flatness, cracks, potholes, bumps, rubble, missing pavement, ruts, and usability for pedestrians, wheelchairs, strollers, or small wheeled mobility devices.\n"
        "Do not judge nearby road, curb, grass, wall, or building unless it is part of the target surface.\n"
        "If the surface is too occluded, too small, blurry, or not visible enough, use smoothness_osm='not_visible' and smoothness_score_1_to_5=null.\n"
        "Do not invent damage that is not visible."
    )
    
    response = model.create_chat_completion(
        messages=[
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Analyze the following properties for this {feature_label}: {list(schema.keys())}. Return the JSON results."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
        max_tokens=300
    )
    
    raw_description = response['choices'][0]['message']['content']
    print(f"InternVL Raw Response for {feature_label}: {raw_description}")
    
    description = raw_description
    # Robust JSON extraction: Find the first { and the corresponding closing }
    try:
        start_idx = description.find("{")
        if start_idx != -1:
            stack = 0
            for i in range(start_idx, len(description)):
                if description[i] == '{':
                    stack += 1
                elif description[i] == '}':
                    stack -= 1
                    if stack == 0:
                        description = description[start_idx : i+1]
                        break
    except Exception as e:
        print(f"Extraction error: {e}")

    # Optional: normalize smoothness_score_1_to_5 from the OSM class
    try:
        parsed = json.loads(description)

        osm_value = parsed.get("smoothness_osm")
        if osm_value in OSM_TO_SCORE:
            parsed["smoothness_score_1_to_5"] = OSM_TO_SCORE[osm_value]

        description = json.dumps(parsed, ensure_ascii=False)

    except Exception as e:
        print(f"JSON normalization error: {e}")

    return description.strip()

def process_internvl(image_path: str, prompt: str):
    """
    Use InternVL to generate a caption/description for the whole image.
    """
    model = get_internvl_model()
    if not model:
        return [{"id": "error", "label": "InternVL model not available.", "confidence": 0, "bbox": {"x": 0, "y": 0, "width": 100, "height": 100}, "color": "#ef4444"}]
        
    image = Image.open(image_path).convert("RGB")
    import base64
    from io import BytesIO
    
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{img_base64}"
    
    print(f"Generating image caption with InternVL...")
    
    # Use the prompt as the question, or a default if empty
    question = prompt if prompt.strip() else "Describe this image in detail."
    
    response = model.create_chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that describes images in detail."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
        max_tokens=200
    )
    
    description = response['choices'][0]['message']['content'].strip()
    
    # Return as a full-image "prediction" so it shows up in the UI
    return [{
        "id": "internvl_gen",
        "label": "InternVL Description",
        "confidence": 1.0,
        "bbox": {"x": 5, "y": 5, "width": 90, "height": 90},
        "description": description,
        "color": "#10b981"
    }]
