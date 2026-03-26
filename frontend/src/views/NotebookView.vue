<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotebookStore } from '@/stores/notebook'
import { useChatStore } from '@/stores/chat'
import { useQuizStore } from '@/stores/quiz'
import NotebookOverview from '@/components/notebook/NotebookOverview.vue'
import CategoryFilter from '@/components/notebook/CategoryFilter.vue'
import EditCategoriesModal from '@/components/notebook/EditCategoriesModal.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import type { Document } from '@/stores/notebook'
import {
  ArrowLeft,
  Upload,
  FileText,
  Send,
  Sparkles,
  MessageSquare,
  HelpCircle,
  ListChecks,
  BookOpen,
  X,
  Loader2,
  Trash2,
  Globe,
  Filter
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const notebookStore = useNotebookStore()
const chatStore = useChatStore()
const quizStore = useQuizStore()

const notebookId = computed(() => route.params.id as string)
const messageInput = ref('')
const messagesContainer = ref<HTMLElement>()
const showUploadModal = ref(false)
const uploadingFile = ref(false)
const fileInput = ref<HTMLInputElement>()

// Web search toggle
const enableWebSearch = ref(false)

// Category filter
const selectedCategories = ref<string[]>([])
const categoryFilterRef = ref<InstanceType<typeof CategoryFilter> | null>(null)

// Notebook Overview ref
const overviewRef = ref<InstanceType<typeof NotebookOverview> | null>(null)

// Saved quizzes
const savedQuizzes = ref<any[]>([])
const loadingQuizzes = ref(false)

// Edit categories modal
const showEditCategoriesModal = ref(false)
const editingDocument = ref<Document | null>(null)

// Filtered documents based on selected categories
const filteredDocuments = computed(() => {
  if (selectedCategories.value.length === 0) {
    return notebookStore.documents
  }
  return notebookStore.documents.filter(doc => {
    if (!doc.categories?.length) return false
    return doc.categories.some(cat => 
      selectedCategories.value.includes(cat.category)
    )
  })
})

function handleCategoryFilter(categories: string[]) {
  selectedCategories.value = categories
}

function openEditCategories(doc: Document) {
  editingDocument.value = doc
  showEditCategoriesModal.value = true
}

function handleCategoriesSaved(categories: string[]) {
  // Refresh documents to get updated categories
  notebookStore.fetchDocuments(notebookId.value)
  // Refresh category filter stats
  if (categoryFilterRef.value) {
    categoryFilterRef.value.refresh()
  }
}

onMounted(async () => {
  await notebookStore.fetchNotebook(notebookId.value)
  chatStore.setNotebook(notebookId.value)
  await loadSavedQuizzes()
})

// Refresh overview when documents change
watch(() => notebookStore.documents.length, () => {
  if (overviewRef.value) {
    overviewRef.value.refresh()
  }
})

async function loadSavedQuizzes() {
  loadingQuizzes.value = true
  try {
    await quizStore.fetchQuizzesByNotebook(notebookId.value)
    savedQuizzes.value = quizStore.quizzes
  } catch (error) {
    console.error('Failed to load quizzes:', error)
  } finally {
    loadingQuizzes.value = false
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function sendMessage() {
  if (!messageInput.value.trim() || chatStore.isLoading) return
  
  const message = messageInput.value
  messageInput.value = ''
  
  await chatStore.sendMessage(message, enableWebSearch.value)
  scrollToBottom()
}

function handleSuggestedQuestion(question: string) {
  chatStore.sendMessage(question, enableWebSearch.value)
  scrollToBottom()
}

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  uploadingFile.value = true
  try {
    await notebookStore.uploadDocument(notebookId.value, file)
    showUploadModal.value = false
  } catch (error) {
    alert('Upload failed. Please try again.')
  } finally {
    uploadingFile.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function deleteDocument(docId: string, event: Event) {
  event.stopPropagation()
  if (confirm('Xóa tài liệu này?')) {
    await notebookStore.deleteDocument(docId)
  }
}

async function generateSummary() {
  messageInput.value = ''
  await chatStore.sendMessage('/summary')
  scrollToBottom()
}

async function generateQuiz() {
  try {
    const quiz = await quizStore.generateQuiz(notebookId.value, 10, 'medium')
    await loadSavedQuizzes() // Refresh quiz list
    router.push(`/quiz/${quiz.id}`)
  } catch (error) {
    alert('Không thể tạo quiz. Hãy đảm bảo notebook có tài liệu.')
  }
}

async function openSavedQuiz(quizId: string) {
  router.push(`/quiz/${quizId}`)
}

async function deleteSavedQuiz(quizId: string, event: Event) {
  event.stopPropagation()
  if (confirm('Xóa quiz này?')) {
    try {
      await quizStore.deleteQuiz(quizId)
      savedQuizzes.value = savedQuizzes.value.filter(q => q.id !== quizId)
    } catch (error) {
      alert('Không thể xóa quiz.')
    }
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<template>
  <div class="h-screen flex flex-col bg-surface-50 bg-gradient-mesh">
    <!-- Header -->
    <header class="glass border-b border-surface-200/50 px-4 py-3 flex items-center gap-4">
      <button
        @click="router.push('/')"
        class="p-2.5 hover:bg-white/50 rounded-xl transition-all duration-200"
      >
        <ArrowLeft class="w-5 h-5 text-surface-600" />
      </button>
      
      <div class="flex-1">
        <h1 class="font-bold text-surface-800 text-lg">
          {{ notebookStore.currentNotebook?.name || 'Loading...' }}
        </h1>
        <p class="text-sm text-surface-500">
          {{ notebookStore.documents.length }} nguồn tài liệu
        </p>
      </div>
      
      <div class="flex items-center gap-2">
        <div class="w-10 h-10 bg-gradient-to-br from-primary-400 to-accent-400 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/20 animate-pulse-slow">
          <Sparkles class="w-5 h-5 text-white" />
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Sidebar - Sources -->
      <aside class="w-80 glass border-r border-surface-200/50 flex flex-col">
        <div class="p-4 border-b border-surface-200/50">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-surface-700 flex items-center gap-2">
              <div class="w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center">
                <FileText class="w-4 h-4 text-white" />
              </div>
              Nguồn tài liệu
            </h2>
            <span class="text-xs text-surface-500">
              {{ filteredDocuments.length }}/{{ notebookStore.documents.length }}
            </span>
          </div>
          
          <!-- Category Filter -->
          <CategoryFilter
            v-if="notebookStore.documents.length > 0"
            ref="categoryFilterRef"
            v-model="selectedCategories"
            :notebook-id="notebookId"
            class="mt-3"
            @filter-change="handleCategoryFilter"
          />
        </div>
        
        <div class="flex-1 overflow-y-auto p-3 space-y-2">
          <div
            v-for="(doc, index) in filteredDocuments"
            :key="doc.id"
            class="group p-3 rounded-xl hover:bg-white/80 cursor-pointer transition-all duration-200 animate-fade-in border border-transparent hover:border-primary-200"
            :style="{ animationDelay: `${index * 0.05}s` }"
            @click="openEditCategories(doc)"
            title="Click để chỉnh sửa phân loại"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gradient-to-br from-orange-400 to-pink-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md">
                <FileText class="w-5 h-5 text-white" />
              </div>
              <span class="text-sm text-surface-700 truncate flex-1 font-medium">{{ doc.filename }}</span>
              <button
                @click="deleteDocument(doc.id, $event)"
                class="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-100 rounded-lg transition-all"
              >
                <Trash2 class="w-4 h-4 text-red-500" />
              </button>
            </div>
            
            <!-- Document Categories -->
            <div v-if="doc.categories?.length" class="mt-2 flex flex-wrap gap-1">
              <span 
                v-for="cat in doc.categories.slice(0, 2)" 
                :key="cat.category"
                class="px-2 py-0.5 text-xs rounded-full"
                :class="{
                  'bg-green-100 text-green-700': cat.confidence === 'high',
                  'bg-yellow-100 text-yellow-700': cat.confidence === 'medium',
                  'bg-gray-100 text-gray-600': cat.confidence === 'low'
                }"
              >
                {{ cat.category.length > 12 ? cat.category.substring(0, 12) + '...' : cat.category }}
              </span>
            </div>
            
            <!-- Key Topics Preview -->
            <div v-if="doc.key_topics?.length" class="mt-1.5 flex flex-wrap gap-1">
              <span 
                v-for="topic in doc.key_topics.slice(0, 3)" 
                :key="topic"
                class="text-xs text-surface-500"
              >
                #{{ topic }}
              </span>
            </div>
          </div>
          
          <!-- Empty State -->
          <div v-if="filteredDocuments.length === 0" class="py-8 text-center">
            <div class="w-16 h-16 bg-surface-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <FileText class="w-8 h-8 text-surface-300" />
            </div>
            <p v-if="notebookStore.documents.length === 0" class="text-surface-400 text-sm">
              Chưa có tài liệu
            </p>
            <p v-else class="text-surface-400 text-sm">
              Không có tài liệu nào khớp với bộ lọc
            </p>
          </div>
        </div>
        
        <div class="p-4 border-t border-surface-200/50">
          <button
            @click="showUploadModal = true"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-surface-300 rounded-xl text-surface-600 hover:border-primary-400 hover:text-primary-600 hover:bg-primary-50/50 transition-all duration-200"
          >
            <Upload class="w-5 h-5" />
            <span class="font-medium">Thêm nguồn</span>
          </button>
        </div>
      </aside>

      <!-- Center - Chat -->
      <main class="flex-1 flex flex-col bg-white/30">
        <!-- Messages -->
        <div 
          ref="messagesContainer"
          class="flex-1 overflow-y-auto p-6 space-y-4"
        >
          <!-- Notebook Overview - Always show when documents exist -->
          <NotebookOverview
            v-if="notebookStore.documents.length > 0"
            ref="overviewRef"
            :notebook-id="notebookId"
            class="mb-6 animate-fade-in"
            @ask-question="handleSuggestedQuestion"
          />

          <!-- Welcome message when no documents -->
          <div v-if="notebookStore.documents.length === 0 && chatStore.messages.length === 0" class="text-center py-16 animate-fade-in">
            <div class="w-20 h-20 bg-gradient-to-br from-primary-400 to-accent-400 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary-500/25 animate-float">
              <Sparkles class="w-10 h-10 text-white" />
            </div>
            <h2 class="text-2xl font-bold text-surface-800 mb-3">
              Xin chào! Tôi có thể giúp gì?
            </h2>
            <p class="text-surface-500 max-w-md mx-auto mb-8">
              Hỏi tôi bất cứ điều gì về tài liệu của bạn.
              Tôi sẽ tìm kiếm và trả lời dựa trên nội dung.
            </p>
          </div>
          
          <!-- Messages -->
          <MessageBubble
            v-for="message in chatStore.messages"
            :key="message.id"
            :message-id="message.id"
            :role="message.role"
            :content="message.content"
            :sources="message.sources"
            :citations="message.citations"
            :web-sources="message.webSources"
            :timestamp="message.timestamp?.toString()"
          />
          
          <!-- Loading indicator -->
          <div v-if="chatStore.isLoading" class="flex justify-start animate-fade-in">
            <div class="message-assistant px-5 py-4 flex items-center gap-3">
              <div class="flex gap-1">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
              <span class="text-surface-500">Đang suy nghĩ...</span>
            </div>
          </div>
        </div>
        
        <!-- Input Area -->
        <div class="border-t border-surface-200/50 p-4 glass">
          <!-- Web Search Toggle -->
          <div class="flex items-center justify-end mb-2">
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <span class="text-surface-500">Tìm kiếm web</span>
              <div class="relative">
                <input 
                  type="checkbox" 
                  v-model="enableWebSearch" 
                  class="sr-only peer"
                />
                <div class="w-9 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500"></div>
              </div>
              <Globe class="w-4 h-4" :class="enableWebSearch ? 'text-blue-500' : 'text-surface-400'" />
            </label>
          </div>
          
          <div class="flex gap-3">
            <input
              v-model="messageInput"
              type="text"
              placeholder="Hỏi về tài liệu của bạn..."
              class="input-modern flex-1"
              @keyup.enter="sendMessage"
              :disabled="chatStore.isLoading"
            />
            <button
              @click="sendMessage"
              :disabled="!messageInput.trim() || chatStore.isLoading"
              class="btn-primary px-5 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send class="w-5 h-5" />
            </button>
          </div>
        </div>
      </main>

      <!-- Right Sidebar - Studio -->
      <aside class="w-80 glass border-l border-surface-200/50 flex flex-col">
        <div class="p-4 border-b border-surface-200/50">
          <h2 class="font-semibold text-surface-700 flex items-center gap-2">
            <div class="w-8 h-8 bg-gradient-to-br from-accent-400 to-pink-500 rounded-lg flex items-center justify-center">
              <Sparkles class="w-4 h-4 text-white" />
            </div>
            AI Studio
          </h2>
        </div>
        
        <div class="flex-1 overflow-y-auto">
          <!-- Tools Section -->
          <div class="p-4 space-y-3 border-b border-surface-200/50">
            <p class="text-sm text-surface-500 mb-4">
              ✨ Công cụ AI phân tích tài liệu
            </p>
            
            <button
              @click="generateSummary"
              :disabled="chatStore.isLoading || notebookStore.documents.length === 0"
              class="group w-full flex items-center gap-3 p-4 rounded-xl border border-surface-200 hover:bg-white hover:border-blue-300 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div class="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <BookOpen class="w-6 h-6 text-white" />
              </div>
              <div class="text-left">
                <p class="font-semibold text-surface-700">Tóm tắt</p>
                <p class="text-xs text-surface-500">Tóm tắt nội dung chính</p>
              </div>
            </button>
            
            <button
              @click="chatStore.sendMessage('/faq 5')"
              :disabled="chatStore.isLoading || notebookStore.documents.length === 0"
              class="group w-full flex items-center gap-3 p-4 rounded-xl border border-surface-200 hover:bg-white hover:border-purple-300 hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div class="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <HelpCircle class="w-6 h-6 text-white" />
              </div>
              <div class="text-left">
                <p class="font-semibold text-surface-700">FAQ</p>
                <p class="text-xs text-surface-500">Câu hỏi thường gặp</p>
              </div>
            </button>
            
            <button
              @click="generateQuiz"
              :disabled="quizStore.isLoading || notebookStore.documents.length === 0"
              class="group w-full flex items-center gap-3 p-4 rounded-xl border border-surface-200 hover:bg-white hover:border-green-300 hover:shadow-lg hover:shadow-green-500/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div class="w-12 h-12 bg-gradient-to-br from-green-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <ListChecks class="w-6 h-6 text-white" />
              </div>
              <div class="text-left">
                <p class="font-semibold text-surface-700">Tạo Quiz</p>
                <p class="text-xs text-surface-500">Kiểm tra kiến thức</p>
              </div>
            </button>
          </div>
          
          <!-- Saved Quizzes Section -->
          <div class="p-4">
            <h3 class="font-semibold text-surface-700 flex items-center gap-2 mb-4">
              <div class="w-6 h-6 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
                <ListChecks class="w-3 h-3 text-white" />
              </div>
              Quiz đã lưu
            </h3>
            
            <div v-if="loadingQuizzes" class="flex items-center justify-center py-8">
              <div class="relative w-10 h-10">
                <div class="absolute inset-0 rounded-full border-2 border-primary-200"></div>
                <div class="absolute inset-0 rounded-full border-2 border-primary-500 border-t-transparent animate-spin"></div>
              </div>
            </div>
            
            <div v-else-if="savedQuizzes.length === 0" class="text-center py-8">
              <div class="w-12 h-12 bg-surface-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                <ListChecks class="w-6 h-6 text-surface-300" />
              </div>
              <p class="text-surface-400 text-sm">Chưa có quiz nào</p>
            </div>
            
            <div v-else class="space-y-2">
              <div
                v-for="(quiz, index) in savedQuizzes"
                :key="quiz.id"
                @click="openSavedQuiz(quiz.id)"
                class="group p-4 rounded-xl border border-surface-200 hover:bg-white hover:border-green-300 hover:shadow-md cursor-pointer transition-all duration-200 animate-fade-in"
                :style="{ animationDelay: `${index * 0.05}s` }"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-surface-700">
                      📝 {{ quiz.total_questions }} câu hỏi
                    </p>
                    <p class="text-xs text-surface-500 mt-1">
                      {{ formatDate(quiz.created_at) }}
                    </p>
                    <div class="flex items-center gap-2 mt-2">
                      <span class="text-xs px-2.5 py-1 rounded-full font-medium" 
                        :class="{
                          'bg-green-100 text-green-700': quiz.difficulty === 'easy',
                          'bg-amber-100 text-amber-700': quiz.difficulty === 'medium',
                          'bg-red-100 text-red-700': quiz.difficulty === 'hard'
                        }">
                        {{ quiz.difficulty === 'easy' ? '🟢 Dễ' : quiz.difficulty === 'medium' ? '🟡 Trung bình' : '🔴 Khó' }}
                      </span>
                    </div>
                  </div>
                  <button
                    @click="deleteSavedQuiz(quiz.id, $event)"
                    class="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-100 rounded-lg transition-all"
                  >
                    <Trash2 class="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Upload Modal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div 
          v-if="showUploadModal"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          @click.self="showUploadModal = false"
        >
          <div class="glass bg-white rounded-3xl w-full max-w-md p-8 animate-scale-in shadow-2xl">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h2 class="text-2xl font-bold text-surface-800">Tải lên tài liệu</h2>
                <p class="text-surface-500 text-sm mt-1">Thêm nguồn cho notebook</p>
              </div>
              <button @click="showUploadModal = false" class="p-2.5 hover:bg-surface-100 rounded-xl transition-all">
                <X class="w-5 h-5 text-surface-500" />
              </button>
            </div>
            
            <div class="border-2 border-dashed border-surface-300 rounded-2xl p-10 text-center hover:border-primary-400 hover:bg-primary-50/30 transition-all duration-300 cursor-pointer" @click="fileInput?.click()">
              <div class="w-16 h-16 bg-gradient-to-br from-primary-400 to-accent-400 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                <Upload class="w-8 h-8 text-white" />
              </div>
              <p class="text-surface-700 font-medium mb-2">Kéo thả file hoặc click để chọn</p>
              <p class="text-sm text-surface-400">PDF, DOCX, TXT (tối đa 50MB)</p>
              
              <input
                ref="fileInput"
                type="file"
                accept=".pdf,.docx,.txt"
                class="hidden"
                @change="handleFileUpload"
              />
            </div>
            
            <button
              @click="fileInput?.click()"
              :disabled="uploadingFile"
              class="btn-primary w-full mt-6 px-6 py-3 disabled:opacity-50"
            >
              <span v-if="uploadingFile" class="flex items-center justify-center gap-2">
                <Loader2 class="w-5 h-5 animate-spin" />
                Đang tải lên...
              </span>
              <span v-else>Chọn file</span>
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
    
    <!-- Edit Categories Modal -->
    <EditCategoriesModal
      v-if="editingDocument"
      :is-open="showEditCategoriesModal"
      :document-id="editingDocument.id"
      :document-name="editingDocument.filename"
      :current-categories="editingDocument.categories || []"
      @close="showEditCategoriesModal = false"
      @save="handleCategoriesSaved"
    />
  </div>
</template>
