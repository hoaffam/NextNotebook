<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, XCircle, Circle } from 'lucide-vue-next'

const props = defineProps<{
  index: number
  question: string
  options: string[]
  selectedAnswer?: string
  correctAnswer?: string
  showResult?: boolean
  explanation?: string
}>()

const emit = defineEmits<{
  select: [letter: string]
}>()

function getOptionLetter(index: number): string {
  return String.fromCharCode(65 + index) // A, B, C, D
}

function isSelected(index: number): boolean {
  return props.selectedAnswer === getOptionLetter(index)
}

function isCorrect(index: number): boolean {
  return props.correctAnswer === getOptionLetter(index)
}

function getOptionClass(index: number) {
  const letter = getOptionLetter(index)
  
  if (!props.showResult) {
    return isSelected(index)
      ? 'border-primary-500 bg-primary-50'
      : 'border-surface-200 hover:border-surface-300 hover:bg-surface-50'
  }
  
  // Show results
  if (isCorrect(index)) {
    return 'border-green-500 bg-green-50'
  }
  
  if (isSelected(index) && !isCorrect(index)) {
    return 'border-red-500 bg-red-50'
  }
  
  return 'border-surface-200 opacity-60'
}

function getLetterClass(index: number) {
  const letter = getOptionLetter(index)
  
  if (!props.showResult) {
    return isSelected(index)
      ? 'bg-primary-500 text-white'
      : 'bg-surface-200 text-surface-600'
  }
  
  if (isCorrect(index)) {
    return 'bg-green-500 text-white'
  }
  
  if (isSelected(index) && !isCorrect(index)) {
    return 'bg-red-500 text-white'
  }
  
  return 'bg-surface-200 text-surface-400'
}
</script>

<template>
  <div class="bg-white rounded-2xl p-6 border border-surface-200 shadow-sm">
    <!-- Question Number -->
    <div class="flex items-center gap-2 mb-4">
      <span class="px-2.5 py-1 bg-primary-100 text-primary-700 text-sm font-medium rounded-full">
        Câu {{ index }}
      </span>
    </div>
    
    <!-- Question Text -->
    <h3 class="text-lg font-medium text-surface-800 mb-6">
      {{ question }}
    </h3>
    
    <!-- Options -->
    <div class="space-y-3">
      <button
        v-for="(option, optIndex) in options"
        :key="optIndex"
        @click="!showResult && emit('select', getOptionLetter(optIndex))"
        :disabled="showResult"
        class="w-full p-4 rounded-xl border-2 text-left transition-all"
        :class="getOptionClass(optIndex)"
      >
        <div class="flex items-start gap-3">
          <!-- Letter Circle -->
          <span 
            class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0 transition-colors"
            :class="getLetterClass(optIndex)"
          >
            {{ getOptionLetter(optIndex) }}
          </span>
          
          <!-- Option Text -->
          <span class="flex-1 pt-1 text-surface-700">{{ option }}</span>
          
          <!-- Result Icons -->
          <CheckCircle2 
            v-if="showResult && isCorrect(optIndex)"
            class="w-5 h-5 text-green-500 flex-shrink-0"
          />
          <XCircle 
            v-else-if="showResult && isSelected(optIndex) && !isCorrect(optIndex)"
            class="w-5 h-5 text-red-500 flex-shrink-0"
          />
        </div>
      </button>
    </div>
    
    <!-- Explanation (after submit) -->
    <div 
      v-if="showResult && explanation"
      class="mt-6 p-4 bg-surface-50 rounded-xl border border-surface-100"
    >
      <p class="text-sm font-medium text-surface-700 mb-2 flex items-center gap-2">
        <span>📖</span>
        Giải thích:
      </p>
      <p class="text-sm text-surface-600 leading-relaxed">
        {{ explanation }}
      </p>
    </div>
  </div>
</template>
