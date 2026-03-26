<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next'

defineProps<{
  size?: 'sm' | 'md' | 'lg'
  text?: string
}>()

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12'
}
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3">
    <Loader2 
      :class="[sizeClasses[size || 'md'], 'animate-spin text-primary-600']" 
    />
    <p v-if="text" class="text-sm text-surface-600">{{ text }}</p>
  </div>
</template>
