<script setup lang="ts">
import { ref, computed } from 'vue';
import Header from './components/Header.vue';
import ImageDropzone, { type Prediction } from './components/ImageDropzone.vue';
import ModelSelector from './components/ModelSelector.vue';
import PromptInput from './components/PromptInput.vue';
import PromptPresets, { type PromptPreset } from './components/PromptPresets.vue';

const selectedImage = ref<File | null>(null);
const selectedModel = ref('grounding-dino');
const promptText = ref('');
const isProcessing = ref(false);
const inferenceResult = ref<string | null>(null);
const predictions = ref<Prediction[]>([]);
const activePresetId = ref<string | null>(null);
const autoEnrich = ref(false);

const promptPresets: PromptPreset[] = [
  {
    id: 'pedestrian_surface',
    name: 'Pedestrian Surface',
    primary: ['sidewalk', 'pavement', 'footway', 'pedestrian walkway'],
    material: {
      asphalt: [],
      concrete: [],
      concrete_plates: [],
      paving_stones: [],
      paving_slabs: [],
      sett: [],
      cobblestone: [],
      unhewn_cobblestone: [],
      bricks: [],
      stone: [],
      gravel: [],
      fine_gravel: [],
      compacted: [],
      dirt: [],
      ground: [],
      grass: [],
      sand: [],
      mud: [],
      wood: [],
      metal: []
    },
    smoothness: ['excellent', 'good', 'intermediate', 'bad', 'very_bad', 'horrible', 'very_horrible', 'impassable']
  },
  {
    id: 'road_surface',
    name: 'Road Surface',
    primary: ['road', 'street', 'highway', 'lane'],
    material: {
      asphalt: [],
      concrete: [],
      concrete_plates: [],
      paving_stones: [],
      paving_slabs: [],
      sett: [],
      cobblestone: [],
      unhewn_cobblestone: [],
      bricks: [],
      stone: [],
      gravel: [],
      fine_gravel: [],
      compacted: [],
      dirt: [],
      ground: [],
      grass: [],
      sand: [],
      mud: [],
      wood: [],
      metal: []
    },
    smoothness: ['excellent', 'good', 'intermediate', 'bad', 'very_bad', 'horrible', 'very_horrible', 'impassable']
  },
  {
    id: 'buildings',
    name: 'Buildings',
    primary: ['building', 'house', 'structure', 'warehouse'],
    material: {
      brick: [],
      concrete: [],
      reinforced_concrete: [],
      stone: [],
      sandstone: [],
      limestone: [],
      granite: [],
      wood: [],
      timber_framing: [],
      steel: [],
      glass: [],
      metal: [],
      plaster: [],
      adobe: [],
      mud: [],
      clay: [],
      rammed_earth: [],
      prefab: [],
      block: [],
      other: []
    }
  },
  {
    id: 'roofs',
    name: 'Roofs',
    primary: ['roof', 'rooftop'],
    material: {
      tile: [],
      roof_tiles: [],
      concrete: [],
      metal: [],
      steel: [],
      aluminium: [],
      zinc: [],
      copper: [],
      slate: [],
      stone: [],
      thatch: [],
      wood: [],
      shingle: [],
      bitumen: [],
      asphalt: [],
      glass: [],
      plastic: [],
      eternit: [],
      solar_panels: [],
      other: []
    },
    smoothness: ['excellent', 'good', 'intermediate', 'bad', 'very_bad', 'horrible', 'very_horrible', 'impassable']
  },
  {
    id: 'people',
    name: 'People',
    primary: ['person', 'man', 'woman', 'child', 'crowd', 'pedestrian']
  },
  {
    id: 'vehicles',
    name: 'Vehicles',
    primary: ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'van']
  },
  {
    id: 'vegetation',
    name: 'Vegetation',
    primary: ['tree', 'bush', 'grass', 'plant', 'forest', 'foliage']
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure',
    primary: ['bridge', 'tunnel', 'road', 'street light', 'sign', 'utility pole']
  }
];

const handlePresetSelect = (prompt: string, presetId: string) => {
  activePresetId.value = presetId;
  promptText.value = prompt;
};

const handlePromptInput = (val: string) => {
  promptText.value = val;
  // If the user manually edits, clear the active preset highlight
  activePresetId.value = null;
};

const canSubmit = computed(() => {
  return selectedImage.value !== null && promptText.value.trim() !== '';
});

const handleInference = async () => {
  if (!canSubmit.value) return;
  
  isProcessing.value = true;
  inferenceResult.value = null;
  predictions.value = [];
  
  const formData = new FormData();
  formData.append('image', selectedImage.value as File);
  formData.append('model', selectedModel.value);
  formData.append('prompt', promptText.value);

  try {
    const response = await fetch('http://localhost:8000/api/predict', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    
    const modelNames: Record<string, string> = {
      'grounding-dino': 'Grounding DINO',
      'sam-3': 'SAM 3',
      'internvl': 'InternVL'
    };
    
    if (data.status === 'success') {
      predictions.value = data.predictions.map((p: any) => ({
        ...p,
        description: '',
        isDescribing: false
      }));
      const statusPrefix = data.mocked ? "(MOCKED) " : "";
      const modelName = modelNames[selectedModel.value] || 'AI Model';
      
      const totalCount = predictions.value.length;
      inferenceResult.value = `${statusPrefix}Detection complete using ${modelName}. Found ${totalCount} results for: "${promptText.value}".`;
      
      // Auto-Enrich logic
      if (autoEnrich.value && predictions.value.length > 0 && selectedModel.value !== 'internvl') {
        predictions.value.forEach(pred => handleDescribe(pred));
      }
    } else {
      throw new Error("API returned failure status");
    }
  } catch (error) {
    console.error("Inference Error:", error);
    inferenceResult.value = `Error: Failed to perform inference. Make sure the Python backend is running.`;
  } finally {
    isProcessing.value = false;
  }
};

const handleDescribe = async (prediction: Prediction) => {
  if (!selectedImage.value) return;
  
  prediction.isDescribing = true;
  
  const formData = new FormData();
  formData.append('image', selectedImage.value);
  formData.append('bbox', JSON.stringify(prediction.bbox));
  formData.append('label', prediction.label); // Pass label context
  
  try {
    const response = await fetch('http://localhost:8000/api/describe', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) throw new Error('Description failed');
    
    const data = await response.json();
    console.log(`[InternVL] Result for ${prediction.label}:`, data);
    
    if (data.status === 'success') {
      prediction.description = data.description;
      
      // Update summary with enrichment count
      const enrichedCount = predictions.value.filter(p => p.description).length;
      const totalCount = predictions.value.length;
      
      const modelNames: Record<string, string> = {
        'grounding-dino': 'Grounding DINO',
        'sam-3': 'SAM 3',
        'internvl': 'InternVL'
      };
      const modelName = modelNames[selectedModel.value] || 'AI Model';
      const statusPrefix = inferenceResult.value?.startsWith("(MOCKED)") ? "(MOCKED) " : "";
      
      inferenceResult.value = `${statusPrefix}Detection complete using ${modelName}. Enriched ${enrichedCount}/${totalCount} objects with InternVL analysis.`;
    }
  } catch (error) {
    console.error("Description Error:", error);
    prediction.description = "Error generating description.";
  } finally {
    prediction.isDescribing = false;
  }
};

const resetInference = () => {
  inferenceResult.value = null;
  predictions.value = [];
};

const formatConf = (val: number) => `${(val * 100).toFixed(0)}%`;

const parseOSMTags = (desc: string) => {
  if (!desc) return null;
  try {
    // If it's already an object
    if (typeof desc === 'object') return desc;
    
    let jsonStr = desc.trim();
    
    // Remove markdown code blocks if present
    if (jsonStr.includes('```')) {
      const match = jsonStr.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
      if (match && match[1]) {
        jsonStr = match[1].trim();
      }
    }
    
    // Safety check for repeated JSON objects
    if (jsonStr.includes('}{')) {
      jsonStr = jsonStr.substring(0, jsonStr.indexOf('}') + 1);
    }
    
    // Extract first {...}
    const start = jsonStr.indexOf('{');
    const end = jsonStr.lastIndexOf('}');
    if (start !== -1 && end !== -1 && end > start) {
      jsonStr = jsonStr.substring(start, end + 1);
    }
    
    return JSON.parse(jsonStr);
  } catch (e) {
    // If it's not JSON, it will fall back to raw display in the template
    return null;
  }
};

</script>

<template>
  <div class="app-container animate-fade-in">
    <Header />
    
    <main class="main-content">
      <div class="split-layout">
        <div class="left-panel">
          <ImageDropzone 
            v-model="selectedImage" 
            :predictions="predictions" 
            @update:modelValue="resetInference"
            @describe="handleDescribe"
          />
          
          <div v-if="inferenceResult" class="results-panel glass-panel animate-fade-in mt-4">
            <div class="results-header">
              <div class="header-main">
                <div class="success-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 class="results-title">Inference Complete</h3>
              </div>
            </div>
            <p class="results-text">{{ inferenceResult }}</p>

            <!-- Detailed Object Analysis -->
            <div v-if="predictions.length > 0" class="findings-list mt-6">
              <h4 class="findings-title">Detailed Object Analysis</h4>
              <div v-for="pred in predictions" :key="`finding-${pred.id}`" class="finding-item animate-fade-in">
                <div class="finding-dot" :style="{ backgroundColor: pred.color }"></div>
                <div class="finding-content">
                  <div class="finding-meta">
                    <span class="finding-label">{{ pred.label }}</span>
                    <span class="finding-conf">{{ formatConf(pred.confidence) }}</span>
                  </div>
                  <div v-if="pred.isDescribing" class="finding-loading">
                    <span class="pulse-dot"></span> Analyzing...
                  </div>
                  <p v-else-if="pred.description" class="finding-desc-tags">
                    <template v-if="parseOSMTags(pred.description)">
                      <span class="osm-tag-group">
                        <!-- Standard Feature Tag -->
                        <span class="osm-tag feature">
                          <span class="tag-key">feature</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).feature }}</span>
                        </span>
                        
                        <!-- Building/Roof Specific Tags -->
                        <template v-if="parseOSMTags(pred.description).purpose || parseOSMTags(pred.description).floors || parseOSMTags(pred.description).flat">
                          <span v-if="parseOSMTags(pred.description).purpose" class="osm-tag landuse">
                            <span class="tag-key">purpose</span>
                            <span class="tag-val">{{ parseOSMTags(pred.description).purpose }}</span>
                          </span>
                          <span v-if="parseOSMTags(pred.description).floors !== undefined" class="osm-tag floors">
                            <span class="tag-key">floors</span>
                            <span class="tag-val">{{ parseOSMTags(pred.description).floors }}</span>
                          </span>
                          <span v-if="parseOSMTags(pred.description).flat" class="osm-tag flat">
                            <span class="tag-key">flat</span>
                            <span class="tag-val">{{ parseOSMTags(pred.description).flat }}</span>
                          </span>
                        </template>

                        <!-- Material Tag -->
                        <span v-if="parseOSMTags(pred.description).material" class="osm-tag surface">
                          <span class="tag-key">material</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).material }}</span>
                        </span>

                        <span v-if="parseOSMTags(pred.description).surface" class="osm-tag surface">
                          <span class="tag-key">surface</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).surface }}</span>
                        </span>
                        
                        <!-- Road Specific Tags -->
                        <span v-if="parseOSMTags(pred.description).smoothness" class="osm-tag smoothness">
                          <span class="tag-key">smoothness</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).smoothness }}</span>
                        </span>
                        <span v-if="parseOSMTags(pred.description).wetness" class="osm-tag wetness">
                          <span class="tag-key">wetness</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).wetness }}</span>
                        </span>
                        <span v-if="parseOSMTags(pred.description).ruts" class="osm-tag ruts">
                          <span class="tag-key">ruts</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).ruts }}</span>
                        </span>
                        <span v-if="parseOSMTags(pred.description).rut_severity && parseOSMTags(pred.description).rut_severity !== 'none'" class="osm-tag rut-severity">
                          <span class="tag-key">severity</span>
                          <span class="tag-val">{{ parseOSMTags(pred.description).rut_severity }}</span>
                        </span>

                        <!-- Generic Description for 'Other' objects -->
                        <span v-if="parseOSMTags(pred.description).description" class="osm-tag-description">
                           <span class="desc-label">General summary:</span> {{ parseOSMTags(pred.description).description }}
                        </span>
                      </span>
                    </template>
                    <template v-else>
                      {{ pred.description }}
                    </template>
                  </p>
                  <button v-else-if="selectedModel !== 'internvl'" class="enrich-btn" @click="handleDescribe(pred)">
                    Enrich with InternVL
                  </button>
                </div>
              </div>
            </div>

            <div class="mock-bbox-overlay" v-if="selectedImage">
              <!-- This is a decorative visualization to simulate results -->
              <div class="pulse-ring"></div>
            </div>
          </div>
        </div>
        
        <div class="right-panel">
          <ModelSelector v-model="selectedModel" />

          <div class="options-panel glass-panel mb-4">
            <div class="toggle-group">
              <div class="toggle-info">
                <span class="toggle-label">Auto-Enrich with InternVL</span>
                <span class="toggle-desc">Automatically identify materials using InternVL 3.5</span>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="autoEnrich">
                <span class="slider round"></span>
              </label>
            </div>
          </div>
          
          <div class="prompt-section">
            <h3 class="section-title">Instructions</h3>
            <PromptInput 
              :model-value="promptText" 
              :is-processing="isProcessing"
              :is-disabled="!selectedImage"
              @update:model-value="handlePromptInput"
              @submit="handleInference"
            />
            
            <PromptPresets 
              :presets="promptPresets"
              :active-preset-id="activePresetId"
              :is-disabled="isProcessing || !selectedImage"
              @select="handlePresetSelect"
            />
            <p class="helper-text" v-if="!selectedImage">Please upload an image first to enable inference.</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.split-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: start;
}

@media (max-width: 900px) {
  .split-layout {
    grid-template-columns: 1fr;
  }
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.prompt-section {
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  padding-left: 0.5rem;
}

.helper-text {
  font-size: 0.85rem;
  color: rgba(239, 68, 68, 0.9);
  margin-top: 0.75rem;
  padding-left: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.helper-text::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: var(--danger-color);
  border-radius: 50%;
}

.results-panel {
  padding: 1.5rem;
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
  position: relative;
  overflow: hidden;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.success-icon {
  color: var(--success-color);
  width: 24px;
  height: 24px;
}

.results-title {
  color: var(--success-color);
  font-size: 1.1rem;
  margin: 0;
}

.results-text {
  font-size: 0.95rem;
  line-height: 1.6;
}

.mock-bbox-overlay {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, transparent 70%);
  pointer-events: none;
}

.pulse-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  border: 2px solid rgba(16, 185, 129, 0.5);
}

@keyframes pulse {
  0% { transform: scale(0.5); opacity: 0; }
  50% { opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

.mt-4 {
  margin-top: 1.5rem;
}

/* Toggle Switch Styles */
.options-panel {
  padding: 1.25rem;
}
.toggle-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.toggle-info {
  display: flex;
  flex-direction: column;
}
.toggle-label {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
}
.toggle-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 22px;
  flex-shrink: 0;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.1);
  transition: .4s;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.slider:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
}
input:checked + .slider {
  background-color: var(--accent-color);
  border-color: var(--accent-color);
}
input:focus + .slider {
  box-shadow: 0 0 1px var(--accent-color);
}
input:checked + .slider:before {
  transform: translateX(22px);
}
.slider.round {
  border-radius: 34px;
}
.slider.round:before {
  border-radius: 50%;
}
.mb-4 {
  margin-bottom: 1.5rem;
}
.mt-6 {
  margin-top: 1.5rem;
}

/* Findings List Styles */
.findings-list {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 1.25rem;
}
.findings-title {
  font-size: 0.9rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 1rem;
  letter-spacing: 0.05em;
}
.finding-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.finding-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}
.finding-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}
.finding-content {
  flex: 1;
}
.finding-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
}
.finding-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.95rem;
}
.finding-conf {
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  padding: 1px 6px;
  border-radius: 4px;
}
.finding-desc {
  font-size: 0.88rem;
  line-height: 1.5;
  color: #cbd5e1;
  margin: 0;
}
.finding-loading {
  font-size: 0.85rem;
  color: var(--accent-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.pulse-dot {
  width: 6px;
  height: 6px;
  background-color: var(--accent-color);
  border-radius: 50%;
  animation: pulse-soft 1.5s infinite;
}
@keyframes pulse-soft {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}
.enrich-btn {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: var(--accent-color);
  font-size: 0.8rem;
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.enrich-btn:hover {
  background: rgba(99, 102, 241, 0.2);
  transform: translateY(-1px);
}

/* OSM Tag Styles */
.osm-tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.osm-tag {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  font-size: 0.75rem;
}
.tag-key {
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 6px;
  color: #94a3b8;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  font-weight: 600;
}
.tag-val {
  padding: 2px 8px;
  color: #f1f5f9;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.osm-tag-description {
  display: block;
  font-size: 0.85rem;
  color: #94a3b8;
  font-style: italic;
  margin-top: 0.5rem;
  line-height: 1.4;
  border-left: 2px solid #334155;
  padding-left: 0.75rem;
}

.desc-label {
  font-weight: 600;
  color: #f1f5f9;
  font-style: normal;
  margin-right: 0.25rem;
}

.osm-tag.feature .tag-key {
  color: #10b981; /* Green-ish */
}
.osm-tag.landuse .tag-key {
  color: #a855f7; /* Purple-ish */
}
.osm-tag.floors .tag-key {
  color: #6366f1; /* Indigo-ish */
}
.osm-tag.flat .tag-key {
  color: #14b8a6; /* Teal-ish */
}
.osm-tag.wetness .tag-key {
  color: #0ea5e9; /* Light Blue */
}
.osm-tag.ruts .tag-key {
  color: #ef4444; /* Red */
}
.osm-tag.rut-severity .tag-key {
  color: #f97316; /* Orange */
}
.osm-tag.surface .tag-key {
  color: #38bdf8; /* Blue-ish */
}
.osm-tag.smoothness .tag-key {
  color: #fbbf24; /* Amber-ish */
}
</style>
