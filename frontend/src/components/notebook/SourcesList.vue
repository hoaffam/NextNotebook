<script setup lang="ts">
import { 
  FileText, 
  Upload, 
  Trash2, 
  CheckCircle2, 
  Loader2,
  File,
  FileType,
  FileImage
} from 'lucide-vue-next'

interface Document {
  id: string
  filename: string
  file_type: string
  chunks_count: number
  created_at: string
}

defineProps<{
  documents: Document[]
  selectedIds?: string[]
  loading?: boolean
}>()

const emit = defineEmits<{
  select: [id: string]
  delete: [id: string]
  upload: []
}>()

function getFileIcon(fileType: string) {
  switch (fileType) {
    case 'pdf':
      return FileType
    case 'docx':
    case 'doc':
      return File
    case 'txt':
      return FileText
    default:
      return FileText
  }
}

function getFileColor(fileType: string) {
  switch (fileType) {
    case 'pdf':
      return 'text-red-500 bg-red-50'
    case 'docx':
    case 'doc':
      return 'text-blue-500 bg-blue-50'
    case 'txt':
      return 'text-surface-500 bg-surface-100'
    default:
      return 'text-surface-500 bg-surface-100'
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('vi-VN', { 
    day: '2-digit', 
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="p-4 border-b border-surface-200">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-surface-800 flex items-center gap-2">
          <FileText class="w-4 h-4" />
          Nguồn tài liệu
        </h2>
        <span class="text-xs text-surface-400">{{ documents.length }} file</span>
      </div>
    </div>
    
    <!-- Documents List -->
    <div class="flex-1 overflow-y-auto p-2">
      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-8">
        <Loader2 class="w-6 h-6 text-primary-600 animate-spin" />
      </div>
      
      <!-- Empty State -->
      <div v-else-if="documents.length === 0" class="text-center py-8 px-4">
        <div class="w-12 h-12 bg-surface-100 rounded-xl flex items-center justify-center mx-auto mb-3">
          <FileText class="w-6 h-6 text-surface-400" />
        </div>
        <p class="text-sm text-surface-500 mb-1">Chưa có tài liệu</p>
        <p class="text-xs text-surface-400">Tải lên PDF, DOCX, hoặc TXT</p>
      </div>
      
      <!-- Document Items -->
      <div v-else class="space-y-1">
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="group flex items-center gap-3 p-3 rounded-xl hover:bg-surface-50 cursor-pointer transition-colors"
          :class="{ 'bg-primary-50 hover:bg-primary-100': selectedIds?.includes(doc.id) }"
          @click="emit('select', doc.id)"
        >
          <!-- File Icon -->
          <div 
            class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
            :class="getFileColor(doc.file_type)"
          >
            <component :is="getFileIcon(doc.file_type)" class="w-5 h-5" />
          </div>
          
          <!-- File Info -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-surface-800 truncate">
              {{ doc.filename }}
            </p>
            <p class="text-xs text-surface-400">
              {{ doc.chunks_count }} chunks • {{ formatDate(doc.created_at) }}
            </p>
          </div>
          
          <!-- Selection Indicator -->
          <CheckCircle2 
            v-if="selectedIds?.includes(doc.id)"
            class="w-5 h-5 text-primary-600 flex-shrink-0"
          />
          
          <!-- Delete Button -->
          <button
            v-else
            @click.stop="emit('delete', doc.id)"
            class="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 rounded-lg transition-all"
            title="Xóa"
          >
            <Trash2 class="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>
    </div>
    
    <!-- Upload Button -->
    <div class="p-3 border-t border-surface-200">
      <button
        @click="emit('upload')"
        class="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-surface-300 rounded-xl text-surface-600 hover:border-primary-400 hover:text-primary-600 hover:bg-primary-50 transition-all"
      >
        <Upload class="w-4 h-4" />
        <span class="text-sm font-medium">Thêm nguồn</span>
      </button>
    </div>
  </div>
</template>
