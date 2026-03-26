<script setup lang="ts">
import { AlertTriangle, X } from 'lucide-vue-next'

defineProps<{
  title: string
  message?: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'info'
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const variants = {
  danger: {
    icon: 'bg-red-100 text-red-600',
    button: 'bg-red-600 hover:bg-red-700 text-white'
  },
  warning: {
    icon: 'bg-yellow-100 text-yellow-600',
    button: 'bg-yellow-600 hover:bg-yellow-700 text-white'
  },
  info: {
    icon: 'bg-blue-100 text-blue-600',
    button: 'bg-blue-600 hover:bg-blue-700 text-white'
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl w-full max-w-md mx-4 p-6 animate-slide-up">
      <div class="flex items-start gap-4">
        <div 
          class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
          :class="variants[variant || 'danger'].icon"
        >
          <AlertTriangle class="w-6 h-6" />
        </div>
        
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-surface-800">{{ title }}</h3>
          <p v-if="message" class="text-sm text-surface-600 mt-1">{{ message }}</p>
        </div>
        
        <button
          @click="emit('cancel')"
          class="p-2 hover:bg-surface-100 rounded-lg transition-colors"
        >
          <X class="w-5 h-5 text-surface-400" />
        </button>
      </div>
      
      <div class="flex gap-3 mt-6 justify-end">
        <button
          @click="emit('cancel')"
          class="px-4 py-2 border border-surface-300 text-surface-700 rounded-lg hover:bg-surface-50 transition-colors"
        >
          {{ cancelText || 'Hủy' }}
        </button>
        <button
          @click="emit('confirm')"
          class="px-4 py-2 rounded-lg transition-colors"
          :class="variants[variant || 'danger'].button"
        >
          {{ confirmText || 'Xác nhận' }}
        </button>
      </div>
    </div>
  </div>
</template>
