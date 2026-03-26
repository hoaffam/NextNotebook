<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { BookOpen, FileText, Tag, Lightbulb, ChevronDown, ChevronUp, Loader2, RefreshCw } from 'lucide-vue-next'
import { notebooksApi } from '@/services/api'
import type { NotebookOverview, DocumentSummary } from '@/types'

const props = defineProps<{
  notebookId: string
}>()

const emit = defineEmits<{
  (e: 'ask-question', question: string): void
}>()

const overview = ref<NotebookOverview | null>(null)
const loading = ref(false)
const refreshing = ref(false)
const error = ref<string | null>(null)
const expanded = ref(true)
const showAllDocs = ref(false)
const isCached = ref(false)

async function fetchOverview(forceRefresh = false) {
  if (!props.notebookId) return
  
  if (forceRefresh) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  error.value = null
  
  try {
    const response = await notebooksApi.getOverview(props.notebookId, forceRefresh)
    overview.value = response.data
    isCached.value = response.data.cached || false
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Không thể tải tổng quan'
    console.error('Failed to fetch overview:', e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function askQuestion(question: string) {
  emit('ask-question', question)
}

function getConfidenceColor(confidence: string) {
  switch (confidence) {
    case 'high': return 'bg-green-100 text-green-700'
    case 'medium': return 'bg-yellow-100 text-yellow-700'
    default: return 'bg-gray-100 text-gray-600'
  }
}

onMounted(() => {
  fetchOverview()
})

watch(() => props.notebookId, () => {
  fetchOverview()
})

// Expose refresh method
defineExpose({ refresh: fetchOverview })
</script>

<template>
  <div v-if="overview || loading" class="bg-gradient-to-br from-primary-50 to-white border border-primary-100 rounded-xl mb-4 overflow-hidden">
    <!-- Header -->
    <div 
      class="flex items-center justify-between px-4 py-3 bg-primary-50/50 cursor-pointer hover:bg-primary-100/50 transition-colors"
      @click="expanded = !expanded"
    >
      <div class="flex items-center gap-2">
        <BookOpen class="w-5 h-5 text-primary-600" />
        <h3 class="font-semibold text-primary-800">Tổng quan Notebook</h3>
        <span v-if="overview" class="text-sm text-primary-600">
          ({{ overview.total_sources }} nguồn)
        </span>
        <span v-if="isCached" class="text-xs text-surface-400 ml-1" title="Sử dụng bản cache">
          (cached)
        </span>
      </div>
      <div class="flex items-center gap-1">
        <!-- Refresh button -->
        <button 
          v-if="overview && !loading"
          @click.stop="fetchOverview(true)"
          :disabled="refreshing"
          class="p-1 hover:bg-primary-200 rounded transition-colors"
          title="Tạo lại tổng quan"
        >
          <RefreshCw class="w-4 h-4 text-primary-600" :class="{ 'animate-spin': refreshing }" />
        </button>
        <button class="p-1 hover:bg-primary-200 rounded transition-colors">
          <ChevronUp v-if="expanded" class="w-4 h-4 text-primary-600" />
          <ChevronDown v-else class="w-4 h-4 text-primary-600" />
        </button>
      </div>
    </div>
    
    <!-- Content -->
    <div v-show="expanded" class="p-4">
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <Loader2 class="w-6 h-6 text-primary-500 animate-spin" />
        <span class="ml-2 text-surface-600">Đang tạo tổng quan...</span>
      </div>
      
      <!-- Error -->
      <div v-else-if="error" class="text-red-600 text-sm py-4">
        {{ error }}
      </div>
      
      <!-- Overview Content -->
      <div v-else-if="overview" class="space-y-4">
        <!-- Main Overview -->
        <div class="prose prose-sm max-w-none">
          <p class="text-surface-700 leading-relaxed">{{ overview.overview }}</p>
        </div>
        
        <!-- Main Topics -->
        <div v-if="overview.main_topics?.length" class="flex flex-wrap gap-2">
          <span 
            v-for="topic in overview.main_topics.slice(0, 8)" 
            :key="topic"
            class="px-2 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-medium"
          >
            {{ topic }}
          </span>
        </div>
        
        <!-- Document Summaries -->
        <div v-if="overview.documents?.length" class="border-t border-primary-100 pt-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-sm font-semibold text-surface-700 flex items-center gap-1">
              <FileText class="w-4 h-4" />
              Tài liệu
            </h4>
            <button 
              v-if="overview.documents.length > 2"
              @click="showAllDocs = !showAllDocs"
              class="text-xs text-primary-600 hover:text-primary-700"
            >
              {{ showAllDocs ? 'Thu gọn' : `Xem tất cả (${overview.documents.length})` }}
            </button>
          </div>
          
          <div class="space-y-3">
            <div 
              v-for="doc in (showAllDocs ? overview.documents : overview.documents.slice(0, 2))" 
              :key="doc.id"
              class="p-3 bg-white rounded-lg border border-surface-200 hover:border-primary-200 transition-colors"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1">
                  <p class="font-medium text-surface-800 text-sm">📄 {{ doc.filename }}</p>
                  <p v-if="doc.summary" class="text-xs text-surface-600 mt-1 line-clamp-2">
                    {{ doc.summary }}
                  </p>
                </div>
                
                <!-- Categories -->
                <div v-if="doc.categories?.length" class="flex flex-wrap gap-1 justify-end">
                  <span 
                    v-for="cat in doc.categories.slice(0, 2)" 
                    :key="cat.category"
                    class="px-1.5 py-0.5 rounded text-xs"
                    :class="getConfidenceColor(cat.confidence)"
                  >
                    {{ cat.category.length > 15 ? cat.category.substring(0, 15) + '...' : cat.category }}
                  </span>
                </div>
              </div>
              
              <!-- Key Topics -->
              <div v-if="doc.key_topics?.length" class="flex flex-wrap gap-1 mt-2">
                <Tag class="w-3 h-3 text-surface-400" />
                <span 
                  v-for="topic in doc.key_topics.slice(0, 4)" 
                  :key="topic"
                  class="text-xs text-surface-500"
                >
                  {{ topic }}{{ doc.key_topics.indexOf(topic) < Math.min(doc.key_topics.length, 4) - 1 ? ',' : '' }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Suggested Questions -->
        <div v-if="overview.suggested_questions?.length" class="border-t border-primary-100 pt-4">
          <h4 class="text-sm font-semibold text-surface-700 flex items-center gap-1 mb-3">
            <Lightbulb class="w-4 h-4 text-yellow-500" />
            Câu hỏi gợi ý
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <button
              v-for="(question, idx) in overview.suggested_questions.slice(0, 4)"
              :key="idx"
              @click="askQuestion(question)"
              class="text-left px-3 py-2 bg-white border border-surface-200 rounded-lg text-sm text-surface-700 hover:bg-primary-50 hover:border-primary-200 hover:text-primary-700 transition-colors"
            >
              {{ question }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-else class="text-center py-8 text-surface-500">
        <FileText class="w-12 h-12 mx-auto mb-2 opacity-30" />
        <p>Chưa có tài liệu nào. Upload tài liệu để xem tổng quan!</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
