<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-vue-next'

const props = defineProps<{
  type?: 'success' | 'error' | 'info' | 'warning'
  message: string
  duration?: number
}>()

const emit = defineEmits<{
  close: []
}>()

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertCircle,
  info: Info
}

const styles = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800'
}

const iconStyles = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-yellow-500',
  info: 'text-blue-500'
}

const type = computed(() => props.type || 'info')
const IconComponent = computed(() => icons[type.value])

// Auto dismiss
if (props.duration) {
  setTimeout(() => emit('close'), props.duration)
}
</script>

<template>
  <div 
    class="flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg animate-slide-up"
    :class="styles[type]"
  >
    <component 
      :is="IconComponent" 
      class="w-5 h-5 flex-shrink-0"
      :class="iconStyles[type]"
    />
    <span class="flex-1 text-sm font-medium">{{ message }}</span>
    <button
      @click="emit('close')"
      class="p-1 hover:bg-white/50 rounded transition-colors"
    >
      <X class="w-4 h-4" />
    </button>
  </div>
</template>
