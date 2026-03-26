import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { quizApi } from '@/services/api'

export interface QuizQuestion {
  id: string
  question: string
  options: string[]
  correct_answer: string
  explanation: string
  difficulty: string
}

export interface Quiz {
  id: string
  notebook_id: string
  questions: QuizQuestion[]
  total_questions: number
  difficulty: string
  created_at: string
}

export interface QuizResult {
  quiz_id: string
  score: number
  correct_count: number
  total_questions: number
  results: Array<{
    question_id: string
    user_answer: string | null
    correct_answer: string
    is_correct: boolean
    explanation: string
  }>
}

export const useQuizStore = defineStore('quiz', () => {
  // State
  const currentQuiz = ref<Quiz | null>(null)
  const quizzes = ref<Quiz[]>([])
  const currentQuestionIndex = ref(0)
  const userAnswers = ref<Record<string, string>>({})
  const quizResult = ref<QuizResult | null>(null)
  const isLoading = ref(false)
  const isSubmitted = ref(false)

  // Getters
  const currentQuestion = computed(() => {
    if (!currentQuiz.value) return null
    return currentQuiz.value.questions[currentQuestionIndex.value]
  })

  const progress = computed(() => {
    if (!currentQuiz.value) return 0
    return ((currentQuestionIndex.value + 1) / currentQuiz.value.total_questions) * 100
  })

  const answeredCount = computed(() => Object.keys(userAnswers.value).length)

  // Actions
  async function generateQuiz(
    notebookId: string, 
    numQuestions: number = 10, 
    difficulty: 'easy' | 'medium' | 'hard' = 'medium'
  ) {
    isLoading.value = true
    try {
      const response = await quizApi.generate({
        notebook_id: notebookId,
        num_questions: numQuestions,
        difficulty
      })
      currentQuiz.value = response.data
      currentQuestionIndex.value = 0
      userAnswers.value = {}
      quizResult.value = null
      isSubmitted.value = false
      return response.data
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function fetchQuiz(quizId: string) {
    isLoading.value = true
    try {
      const response = await quizApi.get(quizId)
      currentQuiz.value = response.data
      currentQuestionIndex.value = 0
      userAnswers.value = {}
      quizResult.value = null
      isSubmitted.value = false
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function fetchQuizzesByNotebook(notebookId: string) {
    try {
      const response = await quizApi.listByNotebook(notebookId)
      quizzes.value = response.data
    } catch (error) {
      console.error('Failed to fetch quizzes:', error)
    }
  }

  async function deleteQuiz(quizId: string) {
    try {
      await quizApi.delete(quizId)
      quizzes.value = quizzes.value.filter(q => q.id !== quizId)
      if (currentQuiz.value?.id === quizId) {
        currentQuiz.value = null
      }
    } catch (error) {
      throw error
    }
  }

  function selectAnswer(questionId: string, answer: string) {
    userAnswers.value[questionId] = answer
  }

  function nextQuestion() {
    if (currentQuiz.value && currentQuestionIndex.value < currentQuiz.value.total_questions - 1) {
      currentQuestionIndex.value++
    }
  }

  function previousQuestion() {
    if (currentQuestionIndex.value > 0) {
      currentQuestionIndex.value--
    }
  }

  function goToQuestion(index: number) {
    if (currentQuiz.value && index >= 0 && index < currentQuiz.value.total_questions) {
      currentQuestionIndex.value = index
    }
  }

  async function submitQuiz() {
    if (!currentQuiz.value) return

    isLoading.value = true
    try {
      const response = await quizApi.submit(currentQuiz.value.id, userAnswers.value)
      quizResult.value = response.data
      isSubmitted.value = true
      return response.data
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function resetQuiz() {
    currentQuestionIndex.value = 0
    userAnswers.value = {}
    quizResult.value = null
    isSubmitted.value = false
  }

  return {
    // State
    currentQuiz,
    quizzes,
    currentQuestionIndex,
    userAnswers,
    quizResult,
    isLoading,
    isSubmitted,
    // Getters
    currentQuestion,
    progress,
    answeredCount,
    // Actions
    generateQuiz,
    fetchQuiz,
    fetchQuizzesByNotebook,
    deleteQuiz,
    selectAnswer,
    nextQuestion,
    previousQuestion,
    goToQuestion,
    submitQuiz,
    resetQuiz
  }
})
