<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const models = [
  {
    id: 'grounding-dino',
    name: 'Grounding DINO',
    description: 'Open-set object detection using natural language.',
    iconPath: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  },
  {
    id: 'sam-3',
    name: 'SAM 3',
    description: 'Segment Anything Model for precise object masking.',
    iconPath: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01'
  }
];

const selectModel = (id: string) => {
  emit('update:modelValue', id);
};
</script>

<template>
  <div class="model-selector-container glass-panel">
    <h3 class="section-title">Select Intelligence Model</h3>
    
    <div class="models-grid">
      <div 
        v-for="model in models" 
        :key="model.id"
        class="model-card"
        :class="{ 'is-active': modelValue === model.id }"
        @click="selectModel(model.id)"
      >
        <div class="model-icon-wrapper" :class="{ 'active-icon': modelValue === model.id }">
          <svg class="model-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="model.iconPath" />
          </svg>
        </div>
        <div class="model-info">
          <h4 class="model-name">{{ model.name }}</h4>
          <p class="model-desc">{{ model.description }}</p>
        </div>
        <div class="active-indicator" v-if="modelValue === model.id">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-selector-container {
  padding: 1.5rem;
  margin-top: 1rem;
}

.section-title {
  font-size: 1.1rem;
  margin-bottom: 1.25rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.model-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--panel-border);
  border-radius: var(--border-radius-md);
  padding: 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.model-card:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.model-card.is-active {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--accent-color);
  box-shadow: 0 4px 20px -5px var(--accent-glow);
}

.model-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--accent-color);
  transform: scaleY(0);
  transition: transform var(--transition-normal);
  transform-origin: center;
}

.model-card.is-active::before {
  transform: scaleY(1);
}

.model-icon-wrapper {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
}

.model-icon {
  width: 24px;
  height: 24px;
  color: var(--text-secondary);
  transition: color var(--transition-normal);
}

.model-card:hover .model-icon {
  color: var(--text-primary);
}

.active-icon {
  background: linear-gradient(135deg, var(--accent-color), var(--accent-hover));
  box-shadow: 0 4px 10px var(--accent-glow);
}

.active-icon .model-icon {
  color: white;
}

.model-info {
  flex: 1;
}

.model-name {
  font-size: 1.05rem;
  margin-bottom: 0.25rem;
  font-weight: 500;
  color: var(--text-primary);
}

.model-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.4;
  margin: 0;
}

.model-card.is-active .model-name {
  color: var(--accent-color);
}

.active-indicator {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 20px;
  height: 20px;
  color: var(--accent-color);
  animation: scaleIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes scaleIn {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
