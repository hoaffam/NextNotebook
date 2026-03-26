<script setup lang="ts">
import { 
  BookOpen, 
  Sparkles, 
  HelpCircle, 
  ListChecks, 
  MessageSquare,
  Loader2 
} from 'lucide-vue-next'

defineProps<{
  loading?: boolean
  hasDocuments?: boolean
}>()

const emit = defineEmits<{
  summary: []
  faq: []
  quiz: []
  studyGuide: []
}>()

const tools = [
  {
    id: 'summary',
    name: 'Tóm tắt',
    description: 'Tóm tắt toàn bộ nội dung',
    icon: BookOpen,
    color: 'bg-blue-100 text-blue-600',
    action: 'summary'
  },
  {
    id: 'faq',
    name: 'FAQ',
    description: 'Câu hỏi thường gặp',
    icon: HelpCircle,
    color: 'bg-purple-100 text-purple-600',
    action: 'faq'
  },
  {
    id: 'quiz',
    name: 'Tạo Quiz',
    description: 'Kiểm tra kiến thức',
    icon: ListChecks,
    color: 'bg-green-100 text-green-600',
    action: 'quiz'
  },
  {
    id: 'study',
    name: 'Study Guide',
    description: 'Hướng dẫn học tập',
    icon: MessageSquare,
    color: 'bg-orange-100 text-orange-600',
    action: 'studyGuide'
  }
]

function handleAction(action: string) {
  switch (action) {
    case 'summary':
      emit('summary')
      break
    case 'faq':
      emit('faq')
      break
    case 'quiz':
      emit('quiz')
      break
    case 'studyGuide':
      emit('studyGuide')
      break
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="p-4 border-b border-surface-200">
      <h2 class="font-semibold text-surface-800 flex items-center gap-2">
        <Sparkles class="w-4 h-4" />
        Studio
      </h2>
    </div>
    
    <!-- Tools -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3">
      <p class="text-sm text-surface-500 mb-4">
        Công cụ AI giúp phân tích tài liệu
      </p>
      
      <!-- Tool Buttons -->
      <button
        v-for="tool in tools"
        :key="tool.id"
        @click="handleAction(tool.action)"
        :disabled="loading || !hasDocuments"
        class="w-full flex items-center gap-3 p-3 rounded-xl border border-surface-200 hover:bg-surface-50 hover:border-primary-300 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed group"
      >
        <div 
          class="w-10 h-10 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105"
          :class="tool.color"
        >
          <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
          <component v-else :is="tool.icon" class="w-5 h-5" />
        </div>
        <div>
          <p class="font-medium text-surface-700">{{ tool.name }}</p>
          <p class="text-xs text-surface-500">{{ tool.description }}</p>
        </div>
      </button>
      
      <!-- Hint when no documents -->
      <div v-if="!hasDocuments" class="mt-6 p-4 bg-surface-50 rounded-xl">
        <p class="text-sm text-surface-500 text-center">
          💡 Tải lên tài liệu để sử dụng các công cụ này
        </p>
      </div>
    </div>
    
    <!-- Tips -->
    <div class="p-4 border-t border-surface-200 bg-surface-50">
      <div class="flex items-start gap-2 text-xs text-surface-500">
        <span class="text-lg">💡</span>
        <p>
          Mẹo: Gõ <code class="bg-surface-200 px-1 rounded">/quiz 10 hard</code> 
          để tạo 10 câu hỏi khó
        </p>
      </div>
    </div>
  </div>
</template>
