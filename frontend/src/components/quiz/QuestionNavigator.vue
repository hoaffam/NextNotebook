<script setup lang="ts">
import { computed } from 'vue'

interface Question {
  id: string
  question: string
}

const props = defineProps<{
  questions: Question[]
  currentIndex: number
  userAnswers: Record<string, string>
  results?: Array<{
    question_id: string
    is_correct: boolean
  }>
  showResults?: boolean
}>()

const emit = defineEmits<{
  goto: [index: number]
}>()

function getButtonClass(question: Question, index: number) {
  // Current question
  if (index === props.currentIndex && !props.showResults) {
    return 'bg-primary-600 text-white'
  }
  
  // Show results mode
  if (props.showResults && props.results) {
    const result = props.results.find(r => r.question_id === question.id)
    if (result?.is_correct) {
      return 'bg-green-100 text-green-700 border-green-300'
    }
    if (result && !result.is_correct) {
      return 'bg-red-100 text-red-700 border-red-300'
    }
  }
  
  // Answered
  if (props.userAnswers[question.id]) {
    return 'bg-primary-100 text-primary-700 border-primary-300'
  }
  
  // Default
  return 'bg-surface-100 text-surface-600 border-surface-200 hover:bg-surface-200'
}
</script>

<template>
  <div class="bg-white rounded-xl p-4 border border-surface-200">
    <p class="text-sm font-medium text-surface-700 mb-3">Danh sách câu hỏi:</p>
    
    <div class="flex flex-wrap gap-2">
      <button
        v-for="(question, index) in questions"
        :key="question.id"
        @click="emit('goto', index)"
        class="w-10 h-10 rounded-lg text-sm font-medium border transition-all hover:scale-105"
        :class="getButtonClass(question, index)"
        :title="`Câu ${index + 1}`"
      >
        {{ index + 1 }}
      </button>
    </div>
    
    <!-- Legend -->
    <div class="mt-4 pt-3 border-t border-surface-100 flex flex-wrap gap-4 text-xs text-surface-500">
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-primary-600"></span>
        Đang xem
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-primary-100 border border-primary-300"></span>
        Đã trả lời
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-surface-100 border border-surface-200"></span>
        Chưa trả lời
      </div>
    </div>
  </div>
</template>
