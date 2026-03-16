import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import shutil
import uuid

# Import inference logic
try:
    from inference import process_grounding_dino, process_sam, describe_area, process_internvl
    has_inference = True
except ImportError as e:
    print(f"Warning: Inference module not loaded correctly. Mocking endpoints. Error: {e}")
    has_inference = False

app = FastAPI(title="AI Demonstrator Backend")

# Allow CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Demonstrator API is running"}

@app.post("/api/predict")
async def predict(
    image: UploadFile = File(...),
    model: str = Form(...),
    prompt: str = Form(...)
):
    if not image:
        raise HTTPException(status_code=400, detail="No image provided")
        
    # Save uploaded file temporarily
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(image.filename)[1]
    if not ext:
        ext = ".jpg"
        
    temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        print(f"Processing image {temp_path} with model {model} and prompt: '{prompt}'")
        
        results = []
        if not has_inference:
            # Return mocked data if ML environment isn't fully set up yet
            if model == "sam-3":
                 results = [{
                     "id": "1",
                     "label": f"Mock Segment: {prompt}",
                     "confidence": 0.99,
                     "bbox": {"x": 20, "y": 20, "width": 60, "height": 60},
                     "segment": "20,20 80,20 80,80 50,90 20,80",
                     "color": "#8b5cf6"
                 }]
            else:
                 results = [{
                     "id": "1",
                     "label": f"Mock Box: {prompt}",
                     "confidence": 0.95,
                     "bbox": {"x": 30, "y": 30, "width": 40, "height": 40},
                     "color": "#10b981"
                 }]
            return {"status": "success", "predictions": results, "mocked": True}
            
        # Real Inference
        if model == "grounding-dino":
            results = process_grounding_dino(temp_path, prompt)
        elif model == "sam-3":
            results = process_sam(temp_path, prompt)
        elif model == "internvl":
            results = process_internvl(temp_path, prompt)
        else:
            # Fallback for other models for now
            results = process_grounding_dino(temp_path, prompt)
            
        return {"status": "success", "predictions": results, "mocked": False}
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/describe")
async def describe(
    image: UploadFile = File(...),
    bbox: str = Form(...), # JSON string of bbox {x, y, width, height}
    label: str = Form("object") # Label hint
):
    import json
    bbox_dict = json.loads(bbox)
    
    # Save image for processing
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"{file_id}.jpg")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        if not has_inference:
            return {"status": "success", "description": "InternVL model is not loaded (mocked mode)."}
            
        description = describe_area(temp_path, bbox_dict, label)
        return {"status": "success", "description": description}
    except Exception as e:
        print(f"Error describing area: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
