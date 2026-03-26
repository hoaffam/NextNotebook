<script setup lang="ts">
import { computed } from 'vue'
import { Trophy, Target, Check, X, RotateCcw, BookOpen } from 'lucide-vue-next'

interface QuizResult {
  quiz_id: string
  score: number
  correct_count: number
  total_questions: number
  results: Array<{
    question_id: string
    user_answer: string
    correct_answer: string
    is_correct: boolean
  }>
}

const props = defineProps<{
  result: QuizResult
}>()

const emit = defineEmits<{
  restart: []
  goBack: []
}>()

const scoreColor = computed(() => {
  const score = props.result.score
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
})

const scoreBgColor = computed(() => {
  const score = props.result.score
  if (score >= 80) return 'bg-green-100'
  if (score >= 60) return 'bg-yellow-100'
  return 'bg-red-100'
})

const scoreEmoji = computed(() => {
  const score = props.result.score
  if (score >= 80) return '🎉'
  if (score >= 60) return '👍'
  return '💪'
})

const message = computed(() => {
  const score = props.result.score
  if (score >= 90) return 'Xuất sắc! Bạn đã nắm vững kiến thức!'
  if (score >= 80) return 'Tuyệt vời! Kết quả rất tốt!'
  if (score >= 60) return 'Khá tốt! Hãy ôn lại một số phần.'
  return 'Hãy cố gắng hơn! Xem lại tài liệu nhé.'
})
</script>

<template>
  <div class="bg-white rounded-2xl p-8 border border-surface-200 shadow-lg max-w-md mx-auto text-center">
    <!-- Trophy Icon -->
    <div 
      class="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6"
      :class="scoreBgColor"
    >
      <Trophy class="w-10 h-10" :class="scoreColor" />
    </div>
    
    <!-- Score -->
    <div class="mb-4">
      <span class="text-5xl font-bold" :class="scoreColor">
        {{ result.score.toFixed(0) }}%
      </span>
    </div>
    
    <!-- Emoji & Message -->
    <p class="text-2xl mb-2">{{ scoreEmoji }}</p>
    <p class="text-surface-600 mb-6">{{ message }}</p>
    
    <!-- Stats -->
    <div class="flex justify-center gap-8 mb-8">
      <div class="text-center">
        <div class="flex items-center justify-center gap-1 text-green-600 mb-1">
          <Check class="w-5 h-5" />
          <span class="text-2xl font-bold">{{ result.correct_count }}</span>
        </div>
        <p class="text-sm text-surface-500">Đúng</p>
      </div>
      
      <div class="text-center">
        <div class="flex items-center justify-center gap-1 text-red-600 mb-1">
          <X class="w-5 h-5" />
          <span class="text-2xl font-bold">{{ result.total_questions - result.correct_count }}</span>
        </div>
        <p class="text-sm text-surface-500">Sai</p>
      </div>
      
      <div class="text-center">
        <div class="flex items-center justify-center gap-1 text-surface-600 mb-1">
          <Target class="w-5 h-5" />
          <span class="text-2xl font-bold">{{ result.total_questions }}</span>
        </div>
        <p class="text-sm text-surface-500">Tổng</p>
      </div>
    </div>
    
    <!-- Actions -->
    <div class="flex gap-3">
      <button
        @click="emit('restart')"
        class="flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-surface-300 text-surface-700 rounded-xl hover:bg-surface-50 transition-colors"
      >
        <RotateCcw class="w-4 h-4" />
        Làm lại
      </button>
      <button
        @click="emit('goBack')"
        class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors"
      >
        <BookOpen class="w-4 h-4" />
        Về notebook
      </button>
    </div>
  </div>
</template>
