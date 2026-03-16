# muddyDINO 🦖⛰️

A sophisticated AI/ML demonstrator frontend for object detection and segmentation using **Grounding DINO** and **SAM 3**.

## Features
- **Object Detection**: Use Grounding DINO Swin-T to detect objects via text prompts.
- **Segmentation**: Use SAM 3 (Segment Anything Model) to generate precise masks for detected objects.
- **Modern UI**: Built with Vue 3, TypeScript, and Vite with a sleek glassmorphism aesthetic.

## Project Setup

### 1. Prerequisites
- Node.js (v18+)
- Python 3.10+
- PyTorch (with MPS/CUDA support recommended)

### 2. Frontend Setup
```bash
npm install
npm run dev
```

### 3. Backend Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# For Mac users (MPS/Metal support for InternVL):
CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 4. Download Model Weights
The model weights are large (~1GB total) and are ignored by Git. You must download them manually into the `weights/` directory:

```bash
mkdir -p weights
cd weights

# Download Grounding DINO Swin-T weights (~660MB)
wget https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth

# Download SAM ViT-B weights (~360MB)
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth

# Download InternVL 3.5 8B GGUF weights (~5GB)
wget https://huggingface.co/bartowski/OpenGVLab_InternVL3_5-8B-GGUF/resolve/main/OpenGVLab_InternVL3_5-8B-Q4_K_M.gguf
wget https://huggingface.co/bartowski/OpenGVLab_InternVL3_5-8B-GGUF/resolve/main/mmproj-OpenGVLab_InternVL3_5-8B-f16.gguf

cd ..
```

### 5. Running the Application

To run the full application, you need to start both the backend (AI models) and the frontend (UI) in separate terminal windows.

#### Terminal 1: Backend (Server & AI Models)
```bash
# Activate virtual environment
source venv/bin/activate

# Navigate to backend and start
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
python main.py
```
*The backend server will run on `http://localhost:8000`.*

#### Terminal 2: Frontend (User Interface)
```bash
# From the root directory
npm run dev
```
*The frontend will be available at `http://localhost:5173`.*

### 6. CPU Mode Focus
If you do not have a compatible GPU (MPS or CUDA) or want to force CPU execution, use the `FORCE_CPU` environment variable when starting the backend:
```bash
FORCE_CPU=1 python main.py
```

## Tech Stack
- **Frontend**: Vue 3, TypeScript, Vite, SVG Overlays
- **Backend**: FastAPI, PyTorch, GroundingDINO, Segment-Anything
- **Design**: Vanilla CSS (Modern Dark Mode / Glassmorphism)
