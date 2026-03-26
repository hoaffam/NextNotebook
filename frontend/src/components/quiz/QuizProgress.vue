<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  current: number
  total: number
  answeredCount: number
}>()

const progress = computed(() => (props.current / props.total) * 100)
</script>

<template>
  <div>
    <!-- Progress Info -->
    <div class="flex items-center justify-between text-sm mb-2">
      <span class="text-surface-600">
        Câu <span class="font-semibold text-surface-800">{{ current }}</span> / {{ total }}
      </span>
      <span class="text-surface-500">
        Đã trả lời: {{ answeredCount }}/{{ total }}
      </span>
    </div>
    
    <!-- Progress Bar -->
    <div class="h-2 bg-surface-200 rounded-full overflow-hidden">
      <div 
        class="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-300 ease-out"
        :style="{ width: `${progress}%` }"
      ></div>
    </div>
  </div>
</template>
