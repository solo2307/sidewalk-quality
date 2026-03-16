<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  modelValue: string;
  isProcessing: boolean;
  isDisabled: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'submit'): void;
}>();

const inputRef = ref<HTMLInputElement | null>(null);

const onInput = (e: Event) => {
  const target = e.target as HTMLInputElement;
  emit('update:modelValue', target.value);
};

const onSubmit = () => {
  if (props.modelValue.trim() && !props.isProcessing && !props.isDisabled) {
    emit('submit');
  }
};
</script>

<template>
  <div class="prompt-container glass-panel">
    <div class="prompt-wrapper">
      <div class="input-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input 
        ref="inputRef"
        type="text" 
        class="prompt-input"
        :value="modelValue"
        @input="onInput"
        @keydown.enter="onSubmit"
        placeholder="Enter your prompt here (e.g., 'Find all cars', 'Describe the scene')"
        :disabled="isDisabled || isProcessing"
      />
      <button 
        class="submit-btn" 
        :class="{ 'is-processing': isProcessing, 'is-disabled': !modelValue.trim() || isDisabled }"
        @click="onSubmit"
        :disabled="!modelValue.trim() || isDisabled || isProcessing"
      >
        <span v-if="!isProcessing" class="btn-text">
          Run Inference
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </span>
        <span v-else class="btn-text loading">
          <div class="spinner"></div>
          Processing...
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.prompt-container {
  padding: 0.75rem;
  margin-top: 1rem;
  border-radius: 100px; /* pill shape */
  background: rgba(25, 30, 45, 0.8);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all var(--transition-normal);
}

.prompt-container:focus-within {
  box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 0 0 2px var(--accent-glow);
  transform: translateY(-1px);
}

.prompt-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}

.input-icon {
  position: absolute;
  left: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  pointer-events: none;
}

.input-icon svg {
  width: 20px;
  height: 20px;
}

.prompt-input {
  flex: 1;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 1rem 1rem 1rem 3.5rem !important;
  font-size: 1.1rem !important;
  color: var(--text-primary);
}

.prompt-input::placeholder {
  color: var(--text-secondary);
  font-weight: 400;
}

.submit-btn {
  background: linear-gradient(135deg, var(--accent-color), var(--accent-hover));
  color: white;
  border: none;
  border-radius: 100px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px var(--accent-glow);
  height: 48px;
  margin-right: 0.25rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--accent-glow);
  filter: brightness(1.1);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: none;
  color: var(--text-secondary);
}

.btn-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
