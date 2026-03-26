<script setup lang="ts">
import { AlertCircle, XCircle, RefreshCw } from 'lucide-vue-next'

defineProps<{
  title?: string
  message: string
  type?: 'error' | 'warning'
  retryable?: boolean
}>()

const emit = defineEmits<{
  retry: []
  dismiss: []
}>()
</script>

<template>
  <div 
    class="rounded-xl p-4 border"
    :class="type === 'warning' 
      ? 'bg-yellow-50 border-yellow-200' 
      : 'bg-red-50 border-red-200'"
  >
    <div class="flex gap-3">
      <AlertCircle 
        class="w-5 h-5 flex-shrink-0"
        :class="type === 'warning' ? 'text-yellow-500' : 'text-red-500'"
      />
      <div class="flex-1">
        <h3 
          v-if="title"
          class="font-medium mb-1"
          :class="type === 'warning' ? 'text-yellow-800' : 'text-red-800'"
        >
          {{ title }}
        </h3>
        <p 
          class="text-sm"
          :class="type === 'warning' ? 'text-yellow-700' : 'text-red-700'"
        >
          {{ message }}
        </p>
        
        <div v-if="retryable" class="mt-3 flex gap-2">
          <button
            @click="emit('retry')"
            class="flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
            :class="type === 'warning' 
              ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
              : 'bg-red-100 text-red-700 hover:bg-red-200'"
          >
            <RefreshCw class="w-3 h-3" />
            Thử lại
          </button>
        </div>
      </div>
      
      <button
        @click="emit('dismiss')"
        class="p-1 rounded-lg hover:bg-white/50 transition-colors"
      >
        <XCircle 
          class="w-4 h-4"
          :class="type === 'warning' ? 'text-yellow-500' : 'text-red-500'"
        />
      </button>
    </div>
  </div>
</template>
