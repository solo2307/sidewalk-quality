<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';

export interface Prediction {
  id: string;
  label: string;
  confidence: number;
  bbox: { x: number; y: number; width: number; height: number };
  segment?: string;
  color: string;
  description?: string;
  isDescribing?: boolean;
}

const props = defineProps<{
  modelValue: File | null;
  predictions?: Prediction[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: File | null): void;
  (e: 'describe', prediction: Prediction): void;
}>();

const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const previewUrl = ref<string | null>(null);

// Create object URL for preview
watch(() => props.modelValue, (newFile) => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  if (newFile) {
    previewUrl.value = URL.createObjectURL(newFile);
  } else {
    previewUrl.value = null;
  }
});

const onDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragging.value = true;
};

const onDragLeave = (e: DragEvent) => {
  e.preventDefault();
  isDragging.value = false;
};

const onDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragging.value = false;
  
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0];
    validateAndEmitFile(file);
  }
};

const onFileSelected = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    const file = target.files[0];
    validateAndEmitFile(file);
  }
};

const validateAndEmitFile = (file: File) => {
  if (file.type.startsWith('image/')) {
    emit('update:modelValue', file);
  } else {
    alert('Please upload a valid image file.');
  }
};

const clearImage = () => {
  emit('update:modelValue', null);
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// Image dimensions tracking for accurate prediction overlay scaling
const imageElement = ref<HTMLImageElement | null>(null);
const displayWidth = ref(0);
const displayHeight = ref(0);

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  resizeObserver = new ResizeObserver((entries) => {
    if (entries[0]) {
      const box = entries[0].borderBoxSize?.[0] || entries[0].contentRect;
      displayWidth.value = 'inlineSize' in box ? box.inlineSize : box.width;
      displayHeight.value = 'blockSize' in box ? box.blockSize : box.height;
    }
  });
});

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect();
});

const onImageLoad = () => {
  if (imageElement.value) {
    displayWidth.value = imageElement.value.offsetWidth;
    displayHeight.value = imageElement.value.offsetHeight;
    resizeObserver?.observe(imageElement.value);
  }
};

watch(imageElement, (newEl, oldEl) => {
  if (oldEl && resizeObserver) resizeObserver.unobserve(oldEl);
  if (newEl && newEl.complete) {
    onImageLoad();
  }
});

const onPaste = (e: ClipboardEvent) => {
  if (e.clipboardData?.files && e.clipboardData.files.length > 0) {
    const file = e.clipboardData.files[0];
    validateAndEmitFile(file);
  } else if (e.clipboardData?.items) {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image/') !== -1) {
        const file = items[i].getAsFile();
        if (file) validateAndEmitFile(file);
        break;
      }
    }
  }
};

onMounted(() => {
  window.addEventListener('paste', onPaste);
});

onBeforeUnmount(() => {
  window.removeEventListener('paste', onPaste);
});

const formatX = (pct: number) => (pct * displayWidth.value) / 100;
const formatY = (pct: number) => (pct * displayHeight.value) / 100;

const formatSegment = (segmentStr: string) => {
  if (!segmentStr || displayWidth.value === 0) return "";
  return segmentStr.split(' ').map(pt => {
    const [x, y] = pt.split(',');
    return `${(parseFloat(x) * displayWidth.value) / 100},${(parseFloat(y) * displayHeight.value) / 100}`;
  }).join(' ');
};

const formatConf = (val: number) => `${(val * 100).toFixed(0)}%`;

const triggerFileInput = () => {
  fileInput.value?.click();
};
</script>

<template>
  <div class="dropzone-container glass-panel" :class="{ 'is-dragging': isDragging }"
       @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop">
    
    <input type="file" ref="fileInput" @change="onFileSelected" accept="image/*" class="hidden-input" />
    
    <div v-if="!previewUrl" class="upload-prompt" @click="triggerFileInput">
      <div class="upload-icon-wrapper">
        <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      </div>
      <h3>Drag & Drop your image here</h3>
      <p>or click to browse from your device</p>
      <p>or paste(ctrl/cmd +v) from clipboard</p>
      <span class="supported-formats">Supports JPG, PNG, WEBP</span>
    </div>
    
    <div v-else class="image-preview-container">
      <div class="image-wrapper">
        <img :src="previewUrl" ref="imageElement" alt="Preview" class="image-preview animate-fade-in" @load="onImageLoad" />
        
        <!-- Prediction Overlays (SVG) -->
        <svg v-if="predictions && predictions.length > 0" class="predictions-overlay animate-fade-in" width="100%" height="100%">
          <g v-for="pred in predictions" :key="pred.id">
            <!-- Segment Polygon -->
            <polygon v-if="pred.segment"
                     :points="formatSegment(pred.segment)"
                     :fill="pred.color"
                     fill-opacity="0.3"
                     :stroke="pred.color"
                     stroke-width="1.5"
                     class="segment-polygon" />
                     
            <!-- Bounding Box -->
            <rect :x="formatX(pred.bbox.x)"
                  :y="formatY(pred.bbox.y)"
                  :width="formatX(pred.bbox.width)"
                  :height="formatY(pred.bbox.height)"
                  fill="none"
                  :stroke="pred.color"
                  stroke-width="2"
                  stroke-dasharray="4"
                  class="bbox-rect" />
                  
            <!-- Label Group (clickable) -->
            <g class="clickable-label" @click.stop="emit('describe', pred)" style="pointer-events: auto; cursor: pointer;">
              <!-- Label Background -->
              <rect :x="formatX(pred.bbox.x)"
                    :y="formatY(pred.bbox.y) - 22"
                    :width="pred.label.length * 8 + 40"
                    height="22"
                    :fill="pred.color"
                    rx="4" />
                    
              <!-- Label Text -->
              <text :x="formatX(pred.bbox.x) + 4"
                    :y="formatY(pred.bbox.y) - 6"
                    fill="#ffffff"
                    font-size="12"
                    font-family="Inter, sans-serif"
                    font-weight="600">
                {{ pred.label }} {{ formatConf(pred.confidence) }}
                <tspan v-if="pred.isDescribing" dx="5" fill="#eab308">...</tspan>
              </text>
            </g>
          </g>
        </svg>

        <div class="image-overlay">
          <button class="btn btn-primary replace-btn" @click="triggerFileInput">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Replace Image
          </button>
          <button class="btn clear-btn" @click="clearImage">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dropzone-container {
  width: 100%;
  min-height: 350px;
  position: relative;
  border: 2px dashed rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
  overflow: hidden;
}

.dropzone-container.is-dragging {
  border-color: var(--accent-color);
  background: rgba(99, 102, 241, 0.1);
  box-shadow: 0 0 30px rgba(99, 102, 241, 0.2);
}

.dropzone-container:hover:not(.is-dragging) {
  border-color: rgba(255, 255, 255, 0.25);
  background: rgba(25, 30, 45, 0.8);
}

.hidden-input {
  display: none;
}

.upload-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem;
  cursor: pointer;
  width: 100%;
  height: 100%;
}

.upload-icon-wrapper {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  transition: transform var(--transition-normal);
}

.upload-prompt:hover .upload-icon-wrapper {
  transform: scale(1.05) translateY(-5px);
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-color);
}

.upload-icon {
  width: 40px;
  height: 40px;
  color: var(--text-secondary);
  transition: color var(--transition-normal);
}

.upload-prompt:hover .upload-icon {
  color: var(--accent-color);
}

.upload-prompt h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.upload-prompt p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.supported-formats {
  font-size: 0.8rem;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  color: var(--text-secondary);
}

.image-preview-container {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
}

.image-wrapper {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  max-height: 100%;
}

.image-preview {
  display: block;
  max-width: 100%;
  max-height: 100%;
  box-shadow: var(--shadow-lg);
  position: relative;
  z-index: 1;
}

.predictions-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5;
}

.segment-polygon {
  animation: pulse-fill 2s infinite alternate;
}

@keyframes pulse-fill {
  from { fill-opacity: 0.2; }
  to { fill-opacity: 0.4; }
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  opacity: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  transition: opacity var(--transition-normal);
  backdrop-filter: blur(4px);
  z-index: 10;
  pointer-events: none; /* Add this to allow clicking through the hidden overlay */
}

.image-wrapper:hover .image-overlay {
  opacity: 1;
  pointer-events: auto; /* Re-enable for buttons when visible */
}

.replace-btn {
  gap: 0.5rem;
}

.clear-btn {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 0.75rem;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  transform: translateY(-2px);
}

.label-text {
  cursor: pointer;
  user-select: none;
}
.label-text:hover {
  text-decoration: underline;
}

/* Rich Description Tooltip */
.rich-description-card {
  position: absolute;
  z-index: 50;
  width: 280px;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-left-width: 4px;
  border-radius: var(--border-radius-md);
  padding: 0.85rem;
  margin-top: 10px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
}

.rich-desc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.ai-badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

.close-desc {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  transition: color 0.2s;
}

.close-desc:hover {
  color: white;
}

.rich-desc-text {
  font-size: 0.85rem;
  line-height: 1.5;
  color: #e2e8f0;
  margin: 0;
  font-weight: 400;
}

.animate-slide-up {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
