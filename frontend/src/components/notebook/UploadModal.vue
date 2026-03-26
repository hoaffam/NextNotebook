<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, Upload, FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  notebookId: string
}>()

const emit = defineEmits<{
  close: []
  uploaded: [document: any]
}>()

const fileInput = ref<HTMLInputElement>()
const dragOver = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'idle' | 'uploading' | 'success' | 'error'>('idle')
const errorMessage = ref('')
const selectedFile = ref<File | null>(null)

const acceptedTypes = '.pdf,.docx,.doc,.txt'
const maxFileSize = 50 * 1024 * 1024 // 50MB

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    validateAndSetFile(file)
  }
}

function handleDrop(event: DragEvent) {
  dragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    validateAndSetFile(file)
  }
}

function validateAndSetFile(file: File) {
  // Reset state
  errorMessage.value = ''
  uploadStatus.value = 'idle'
  
  // Check file type
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'docx', 'doc', 'txt'].includes(ext || '')) {
    errorMessage.value = 'Chỉ hỗ trợ file PDF, DOCX, TXT'
    return
  }
  
  // Check file size
  if (file.size > maxFileSize) {
    errorMessage.value = 'File quá lớn (tối đa 50MB)'
    return
  }
  
  selectedFile.value = file
}

async function uploadFile() {
  if (!selectedFile.value) return
  
  uploading.value = true
  uploadStatus.value = 'uploading'
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('notebook_id', props.notebookId)
    
    // Simulated progress (real progress would come from axios)
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)
    
    const response = await fetch(`/api/v1/documents/upload`, {
      method: 'POST',
      body: formData
    })
    
    clearInterval(progressInterval)
    
    if (!response.ok) {
      throw new Error('Upload failed')
    }
    
    const result = await response.json()
    uploadProgress.value = 100
    uploadStatus.value = 'success'
    
    setTimeout(() => {
      emit('uploaded', result)
      emit('close')
    }, 1000)
    
  } catch (error) {
    uploadStatus.value = 'error'
    errorMessage.value = 'Tải lên thất bại. Vui lòng thử lại.'
  } finally {
    uploading.value = false
  }
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="emit('close')">
    <div class="bg-white rounded-2xl w-full max-w-lg mx-4 overflow-hidden animate-slide-up">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-surface-200">
        <h2 class="text-lg font-semibold text-surface-800">Tải lên tài liệu</h2>
        <button
          @click="emit('close')"
          class="p-2 hover:bg-surface-100 rounded-lg transition-colors"
        >
          <X class="w-5 h-5 text-surface-500" />
        </button>
      </div>
      
      <!-- Content -->
      <div class="p-6">
        <!-- Drop Zone -->
        <div
          v-if="!selectedFile"
          @dragover.prevent="dragOver = true"
          @dragleave="dragOver = false"
          @drop.prevent="handleDrop"
          class="border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer"
          :class="dragOver 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-surface-300 hover:border-surface-400'"
          @click="fileInput?.click()"
        >
          <Upload class="w-12 h-12 text-surface-400 mx-auto mb-4" />
          <p class="text-surface-700 font-medium mb-2">
            Kéo thả file hoặc click để chọn
          </p>
          <p class="text-sm text-surface-400">
            Hỗ trợ PDF, DOCX, TXT (tối đa 50MB)
          </p>
          
          <input
            ref="fileInput"
            type="file"
            :accept="acceptedTypes"
            class="hidden"
            @change="handleFileSelect"
          />
        </div>
        
        <!-- Selected File -->
        <div v-else class="border border-surface-200 rounded-xl p-4">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <FileText class="w-6 h-6 text-primary-600" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-surface-800 truncate">{{ selectedFile.name }}</p>
              <p class="text-sm text-surface-400">{{ formatFileSize(selectedFile.size) }}</p>
            </div>
            
            <!-- Status Icons -->
            <div v-if="uploadStatus === 'success'" class="text-green-500">
              <CheckCircle2 class="w-6 h-6" />
            </div>
            <div v-else-if="uploadStatus === 'error'" class="text-red-500">
              <AlertCircle class="w-6 h-6" />
            </div>
            <button
              v-else-if="!uploading"
              @click="selectedFile = null"
              class="p-2 hover:bg-surface-100 rounded-lg transition-colors"
            >
              <X class="w-4 h-4 text-surface-400" />
            </button>
          </div>
          
          <!-- Progress Bar -->
          <div v-if="uploading || uploadStatus === 'success'" class="mt-3">
            <div class="h-2 bg-surface-100 rounded-full overflow-hidden">
              <div 
                class="h-full transition-all duration-300"
                :class="uploadStatus === 'success' ? 'bg-green-500' : 'bg-primary-600'"
                :style="{ width: `${uploadProgress}%` }"
              ></div>
            </div>
            <p class="text-xs text-surface-500 mt-1">
              {{ uploadStatus === 'success' ? 'Hoàn tất!' : `${uploadProgress}%` }}
            </p>
          </div>
        </div>
        
        <!-- Error Message -->
        <p v-if="errorMessage" class="mt-3 text-sm text-red-500 flex items-center gap-2">
          <AlertCircle class="w-4 h-4" />
          {{ errorMessage }}
        </p>
      </div>
      
      <!-- Footer -->
      <div class="flex gap-3 p-4 border-t border-surface-200 bg-surface-50">
        <button
          @click="emit('close')"
          class="flex-1 px-4 py-2.5 border border-surface-300 text-surface-700 rounded-xl hover:bg-white transition-colors"
        >
          Hủy
        </button>
        <button
          @click="uploadFile"
          :disabled="!selectedFile || uploading || uploadStatus === 'success'"
          class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="uploading" class="w-4 h-4 animate-spin" />
          <Upload v-else class="w-4 h-4" />
          <span>{{ uploading ? 'Đang tải...' : 'Tải lên' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
