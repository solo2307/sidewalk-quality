<script setup lang="ts">
import { ref, computed } from 'vue';

export interface PromptPreset {
  id: string;
  name: string;
  primary: string[]; // primary terms
  material?: Record<string, string[]>; // optional material categories
  smoothness?: string[]; // optional smoothness levels
}

const props = defineProps<{
  presets: PromptPreset[];
  activePresetId: string | null;
  isDisabled: boolean;
}>();

const emit = defineEmits<{
  (e: 'select', prompt: string, presetId: string): void;
}>();

// Local state for selections within the active preset
const selectedPrimary = ref<string>('');
const selectedMaterial = ref<string>('');
const selectedSmoothness = ref<string>('');

const activePreset = computed(() =>
  props.presets.find(p => p.id === props.activePresetId) || null
);

const onPresetClick = (presetId: string) => {
  if (props.isDisabled) return;
  // Reset selections when switching preset
  selectedPrimary.value = '';
  selectedMaterial.value = '';
  selectedSmoothness.value = '';
  emit('select', '', presetId); // indicate preset change without prompt yet
};

const updatePrompt = () => {
  const parts = [];
  if (selectedPrimary.value) parts.push(selectedPrimary.value);
  if (selectedMaterial.value) parts.push(selectedMaterial.value);
  if (selectedSmoothness.value) parts.push(selectedSmoothness.value);
  
  emit('select', parts.join(' ').trim(), activePreset.value?.id ?? '');
};

const onPrimarySelect = (term: string) => {
  selectedPrimary.value = term;
  updatePrompt();
};

const onMaterialSelect = (materialTerm: string) => {
  selectedMaterial.value = materialTerm;
  updatePrompt();
};

const onSmoothnessSelect = (smoothTerm: string) => {
  selectedSmoothness.value = smoothTerm;
  updatePrompt();
};
</script>

<template>
  <div class="presets-container">
    <!-- Preset buttons -->
    <div class="presets-label">Quick Prompts</div>
    <div class="presets-grid">
      <button
        v-for="preset in props.presets"
        :key="preset.id"
        class="preset-btn"
        :class="{ 'is-active': props.activePresetId === preset.id, 'is-disabled': props.isDisabled }"
        @click="onPresetClick(preset.id)"
        :disabled="props.isDisabled"
      >
        {{ preset.name }}
      </button>
    </div>

    <!-- Primary terms for the selected preset -->
    <div v-if="activePreset && activePreset.primary.length" class="section-label">Primary terms</div>
    <div v-if="activePreset && activePreset.primary.length" class="presets-grid">
      <button
        v-for="term in activePreset.primary"
        :key="term"
        class="preset-btn"
        :class="{ 'is-active': selectedPrimary === term }"
        @click="onPrimarySelect(term)"
        :disabled="props.isDisabled"
      >{{ term }}</button>
    </div>

    <!-- Material options if available -->
    <div v-if="activePreset && activePreset.material && selectedPrimary" class="section-label">Material</div>
    <div v-if="activePreset && activePreset.material && selectedPrimary" class="presets-grid">
      <button
        v-for="(terms, mat) in activePreset.material"
        :key="mat"
        class="preset-btn"
        :class="{ 'is-active': selectedMaterial === mat }"
        @click="onMaterialSelect(mat)"
        :disabled="props.isDisabled"
      >{{ mat }}</button>
    </div>

    <!-- Smoothness options if available -->
    <div v-if="activePreset && activePreset.smoothness && (selectedPrimary || selectedMaterial)" class="section-label">Smoothness</div>
    <div v-if="activePreset && activePreset.smoothness && (selectedPrimary || selectedMaterial)" class="presets-grid">
      <button
        v-for="smooth in activePreset.smoothness"
        :key="smooth"
        class="preset-btn"
        :class="{ 'is-active': selectedSmoothness === smooth }"
        @click="onSmoothnessSelect(smooth)"
        :disabled="props.isDisabled"
      >{{ smooth }}</button>
    </div>
  </div>
</template>

<style scoped>
.presets-container {
  margin-top: 1rem;
  padding: 0 0.5rem;
}
.presets-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.presets-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.preset-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition-normal);
}
.preset-btn:hover:not(.is-disabled) {
  background: rgba(255, 255, 255, 0.1);
}
.preset-btn.is-active {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}
.preset-btn.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.section-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0.65rem 0 0.35rem 0;
}
</style>
