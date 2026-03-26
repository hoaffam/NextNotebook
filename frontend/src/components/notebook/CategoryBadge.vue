<script setup lang="ts">
import type { CategoryAssignment } from '@/types'

const props = defineProps<{
  category: CategoryAssignment
  size?: 'sm' | 'md'
  showScore?: boolean
}>()

function getConfidenceStyles(confidence: string) {
  switch (confidence) {
    case 'high':
      return 'bg-green-100 text-green-700 border-green-200'
    case 'medium':
      return 'bg-yellow-100 text-yellow-700 border-yellow-200'
    case 'low':
      return 'bg-gray-100 text-gray-600 border-gray-200'
    default:
      return 'bg-gray-100 text-gray-600 border-gray-200'
  }
}

function getCategoryIcon(category: string) {
  // Map categories to icons/emojis
  const iconMap: Record<string, string> = {
    'Computing methodologies': '🤖',
    'Software and its engineering': '💻',
    'Information systems': '📊',
    'Security and privacy': '🔒',
    'Networks': '🌐',
    'Hardware': '🔧',
    'Theory of computation': '📐',
    'Human-centered computing': '👥',
    'Applied computing': '🏭',
    'Business and Management': '💼',
    'Health and Medicine': '🏥',
    'Education and Pedagogy': '📚',
    'Natural Sciences': '🔬',
    'Engineering': '⚙️',
    'Uncategorized': '📁'
  }
  return iconMap[category] || '📄'
}

function truncateCategory(name: string, maxLen = 20) {
  if (name.length <= maxLen) return name
  return name.substring(0, maxLen) + '...'
}
</script>

<template>
  <span 
    class="inline-flex items-center gap-1 rounded-full border transition-colors"
    :class="[
      getConfidenceStyles(category.confidence),
      size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-sm'
    ]"
    :title="`${category.category} (${(category.score * 100).toFixed(0)}% confidence)`"
  >
    <span>{{ getCategoryIcon(category.category) }}</span>
    <span>{{ truncateCategory(category.category) }}</span>
    <span 
      v-if="showScore && category.score" 
      class="opacity-60 text-xs"
    >
      {{ (category.score * 100).toFixed(0) }}%
    </span>
    <span 
      v-if="!category.is_auto" 
      class="text-xs opacity-70"
      title="User assigned"
    >
      ✓
    </span>
  </span>
</template>
