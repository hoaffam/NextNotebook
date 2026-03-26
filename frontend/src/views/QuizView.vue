<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuizStore } from '@/stores/quiz'
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Trophy,
  RotateCcw,
  BookOpen
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const quizStore = useQuizStore()

const quizId = computed(() => route.params.id as string)
const selectedAnswer = ref<string | null>(null)

onMounted(async () => {
  if (quizId.value && !quizStore.currentQuiz) {
    await quizStore.fetchQuiz(quizId.value)
  }
})

function selectOption(option: string, index: number) {
  if (quizStore.isSubmitted) return
  
  const letter = String.fromCharCode(65 + index) // A, B, C, D
  selectedAnswer.value = letter
  
  if (quizStore.currentQuestion) {
    quizStore.selectAnswer(quizStore.currentQuestion.id, letter)
  }
}

function nextQuestion() {
  selectedAnswer.value = null
  quizStore.nextQuestion()
  
  // Restore selected answer if exists
  if (quizStore.currentQuestion) {
    selectedAnswer.value = quizStore.userAnswers[quizStore.currentQuestion.id] || null
  }
}

function previousQuestion() {
  selectedAnswer.value = null
  quizStore.previousQuestion()
  
  // Restore selected answer if exists
  if (quizStore.currentQuestion) {
    selectedAnswer.value = quizStore.userAnswers[quizStore.currentQuestion.id] || null
  }
}

async function submitQuiz() {
  if (confirm('Bạn có chắc muốn nộp bài?')) {
    await quizStore.submitQuiz()
  }
}

function restartQuiz() {
  quizStore.resetQuiz()
  selectedAnswer.value = null
}

function getResultForQuestion(questionId: string) {
  if (!quizStore.quizResult) return null
  return quizStore.quizResult.results.find(r => r.question_id === questionId)
}

const scoreColor = computed(() => {
  if (!quizStore.quizResult) return 'text-surface-600'
  const score = quizStore.quizResult.score
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
})

const scoreEmoji = computed(() => {
  if (!quizStore.quizResult) return '📝'
  const score = quizStore.quizResult.score
  if (score >= 80) return '🎉'
  if (score >= 60) return '👍'
  return '💪'
})
</script>

<template>
  <div class="min-h-screen bg-surface-50 bg-gradient-mesh">
    <!-- Header -->
    <header class="glass border-b border-surface-200/50 px-4 py-3 flex items-center gap-4 sticky top-0 z-10">
      <button
        @click="router.back()"
        class="p-2.5 hover:bg-white/50 rounded-xl transition-all duration-200"
      >
        <ArrowLeft class="w-5 h-5 text-surface-600" />
      </button>
      
      <div class="flex-1">
        <h1 class="font-bold text-surface-800 text-lg flex items-center gap-2">
          <span class="w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-lg flex items-center justify-center">
            🎯
          </span>
          Quiz
        </h1>
        <p class="text-sm text-surface-500 ml-10">
          {{ quizStore.currentQuiz?.difficulty === 'easy' ? '🟢 Dễ' : quizStore.currentQuiz?.difficulty === 'hard' ? '🔴 Khó' : '🟡 Trung bình' }} • 
          {{ quizStore.currentQuiz?.total_questions || 0 }} câu hỏi
        </p>
      </div>
      
      <div v-if="!quizStore.isSubmitted" class="px-4 py-2 bg-primary-50 text-primary-700 rounded-xl text-sm font-medium">
        ✅ {{ quizStore.answeredCount }}/{{ quizStore.currentQuiz?.total_questions || 0 }}
      </div>
    </header>

    <!-- Loading -->
    <div v-if="quizStore.isLoading" class="flex flex-col items-center justify-center py-20">
      <div class="relative w-16 h-16">
        <div class="absolute inset-0 rounded-full border-4 border-primary-200"></div>
        <div class="absolute inset-0 rounded-full border-4 border-primary-500 border-t-transparent animate-spin"></div>
      </div>
      <p class="mt-4 text-surface-500">Đang tải quiz...</p>
    </div>

    <!-- Quiz Content -->
    <main v-else-if="quizStore.currentQuiz" class="max-w-3xl mx-auto px-4 py-8">
      <!-- Results Summary -->
      <div v-if="quizStore.isSubmitted && quizStore.quizResult" class="mb-8 animate-scale-in">
        <div class="card p-8 text-center">
          <div class="w-24 h-24 mx-auto mb-6 bg-gradient-to-br rounded-3xl flex items-center justify-center shadow-xl"
            :class="quizStore.quizResult.score >= 80 ? 'from-green-400 to-emerald-500 shadow-green-500/25' : quizStore.quizResult.score >= 60 ? 'from-yellow-400 to-amber-500 shadow-amber-500/25' : 'from-red-400 to-rose-500 shadow-red-500/25'">
            <Trophy class="w-12 h-12 text-white" />
          </div>
          <p class="text-5xl font-bold mb-2" :class="scoreColor">
            {{ quizStore.quizResult.score.toFixed(0) }}%
          </p>
          <p class="text-surface-600 mb-6 text-lg">
            {{ scoreEmoji }} {{ quizStore.quizResult.correct_count }}/{{ quizStore.quizResult.total_questions }} câu đúng
          </p>
          
          <div class="flex gap-3 justify-center">
            <button
              @click="restartQuiz"
              class="btn-secondary flex items-center gap-2 px-5 py-3"
            >
              <RotateCcw class="w-4 h-4" />
              Làm lại
            </button>
            <button
              @click="router.back()"
              class="btn-primary flex items-center gap-2 px-5 py-3"
            >
              <BookOpen class="w-4 h-4" />
              Về notebook
            </button>
          </div>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="mb-6">
        <div class="flex justify-between text-sm text-surface-600 mb-2">
          <span class="font-medium">Câu {{ quizStore.currentQuestionIndex + 1 }}/{{ quizStore.currentQuiz.total_questions }}</span>
          <span class="font-medium">{{ quizStore.progress.toFixed(0) }}%</span>
        </div>
        <div class="h-3 bg-surface-200 rounded-full overflow-hidden shadow-inner">
          <div 
            class="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-500 ease-out rounded-full"
            :style="{ width: `${quizStore.progress}%` }"
          ></div>
        </div>
      </div>

      <!-- Question Card -->
      <div v-if="quizStore.currentQuestion" class="card p-8 animate-fade-in">
        <!-- Question -->
        <h2 class="text-xl font-semibold text-surface-800 mb-8 leading-relaxed">
          {{ quizStore.currentQuestion.question }}
        </h2>

        <!-- Options -->
        <div class="space-y-4">
          <button
            v-for="(option, index) in quizStore.currentQuestion.options"
            :key="index"
            @click="selectOption(option, index)"
            :disabled="quizStore.isSubmitted"
            class="w-full p-5 rounded-2xl border-2 text-left transition-all duration-300 group"
            :class="[
              quizStore.isSubmitted
                ? getResultForQuestion(quizStore.currentQuestion.id)?.correct_answer === String.fromCharCode(65 + index)
                  ? 'border-green-500 bg-green-50 shadow-lg shadow-green-500/10'
                  : getResultForQuestion(quizStore.currentQuestion.id)?.user_answer === String.fromCharCode(65 + index)
                    ? 'border-red-500 bg-red-50 shadow-lg shadow-red-500/10'
                    : 'border-surface-200'
                : selectedAnswer === String.fromCharCode(65 + index)
                  ? 'border-primary-500 bg-primary-50 shadow-lg shadow-primary-500/10'
                  : 'border-surface-200 hover:border-primary-300 hover:bg-white hover:shadow-md'
            ]"
          >
            <div class="flex items-start gap-4">
              <span class="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0 transition-all duration-300"
                :class="[
                  quizStore.isSubmitted
                    ? getResultForQuestion(quizStore.currentQuestion.id)?.correct_answer === String.fromCharCode(65 + index)
                      ? 'bg-green-500 text-white'
                      : getResultForQuestion(quizStore.currentQuestion.id)?.user_answer === String.fromCharCode(65 + index)
                        ? 'bg-red-500 text-white'
                        : 'bg-surface-200 text-surface-600'
                    : selectedAnswer === String.fromCharCode(65 + index)
                      ? 'bg-primary-500 text-white'
                      : 'bg-surface-200 text-surface-600'
                ]"
              >
                {{ String.fromCharCode(65 + index) }}
              </span>
              <span class="flex-1 pt-1">{{ option }}</span>
              
              <CheckCircle2 
                v-if="quizStore.isSubmitted && getResultForQuestion(quizStore.currentQuestion.id)?.correct_answer === String.fromCharCode(65 + index)"
                class="w-5 h-5 text-green-500 flex-shrink-0"
              />
              <XCircle 
                v-else-if="quizStore.isSubmitted && getResultForQuestion(quizStore.currentQuestion.id)?.user_answer === String.fromCharCode(65 + index) && !getResultForQuestion(quizStore.currentQuestion.id)?.is_correct"
                class="w-5 h-5 text-red-500 flex-shrink-0"
              />
            </div>
          </button>
        </div>

        <!-- Explanation (after submit) -->
        <div 
          v-if="quizStore.isSubmitted && getResultForQuestion(quizStore.currentQuestion.id)"
          class="mt-6 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-100"
        >
          <p class="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
            <span class="w-6 h-6 bg-blue-500 rounded-lg flex items-center justify-center text-white text-xs">💡</span>
            Giải thích
          </p>
          <p class="text-sm text-surface-700 leading-relaxed">
            {{ quizStore.currentQuestion.explanation }}
          </p>
        </div>
      </div>

      <!-- Navigation -->
      <div class="flex items-center justify-between mt-8">
        <button
          @click="previousQuestion"
          :disabled="quizStore.currentQuestionIndex === 0"
          class="btn-secondary flex items-center gap-2 px-5 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft class="w-5 h-5" />
          Trước
        </button>

        <div v-if="!quizStore.isSubmitted" class="flex gap-2">
          <button
            v-if="quizStore.currentQuestionIndex === quizStore.currentQuiz.total_questions - 1"
            @click="submitQuiz"
            :disabled="quizStore.answeredCount < quizStore.currentQuiz.total_questions"
            class="btn-primary bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ✓ Nộp bài
          </button>
        </div>

        <button
          @click="nextQuestion"
          :disabled="quizStore.currentQuestionIndex === quizStore.currentQuiz.total_questions - 1"
          class="btn-secondary flex items-center gap-2 px-5 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Tiếp
          <ChevronRight class="w-5 h-5" />
        </button>
      </div>

      <!-- Question Navigator -->
      <div class="mt-8 card p-6">
        <p class="text-sm font-semibold text-surface-700 mb-4 flex items-center gap-2">
          <span class="w-6 h-6 bg-gradient-to-br from-primary-400 to-accent-400 rounded-lg flex items-center justify-center text-white text-xs">📋</span>
          Danh sách câu hỏi
        </p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="(q, index) in quizStore.currentQuiz.questions"
            :key="q.id"
            @click="quizStore.goToQuestion(index)"
            class="w-11 h-11 rounded-xl text-sm font-bold transition-all duration-200"
            :class="[
              quizStore.isSubmitted
                ? getResultForQuestion(q.id)?.is_correct
                  ? 'bg-gradient-to-br from-green-400 to-emerald-500 text-white shadow-lg shadow-green-500/25'
                  : getResultForQuestion(q.id)
                    ? 'bg-gradient-to-br from-red-400 to-rose-500 text-white shadow-lg shadow-red-500/25'
                    : 'bg-surface-100 text-surface-600 border border-surface-200'
                : quizStore.currentQuestionIndex === index
                  ? 'bg-gradient-to-br from-primary-500 to-accent-500 text-white shadow-lg shadow-primary-500/25'
                  : quizStore.userAnswers[q.id]
                    ? 'bg-primary-100 text-primary-700 border-2 border-primary-400'
                    : 'bg-surface-100 text-surface-600 border border-surface-200 hover:bg-surface-200 hover:border-surface-300'
            ]"
          >
            {{ index + 1 }}
          </button>
        </div>
      </div>
    </main>

    <!-- No Quiz -->
    <div v-else class="text-center py-20 animate-fade-in">
      <div class="w-20 h-20 bg-surface-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
        <span class="text-4xl">🤔</span>
      </div>
      <p class="text-surface-500 text-lg">Quiz không tồn tại</p>
      <button @click="router.back()" class="btn-primary mt-4 px-6 py-2">
        Quay lại
      </button>
      <button
        @click="router.back()"
        class="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
      >
        Quay lại
      </button>
    </div>
  </div>
</template>
