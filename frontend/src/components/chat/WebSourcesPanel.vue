<script setup lang="ts">
import { Globe, ExternalLink, ChevronDown, ChevronUp } from 'lucide-vue-next'
import { ref } from 'vue'
import type { WebSource } from '@/types'

const props = defineProps<{
  sources: WebSource[]
}>()

const expanded = ref(true)

function truncateContent(content: string, maxLen = 150) {
  if (content.length <= maxLen) return content
  return content.substring(0, maxLen) + '...'
}

function getDomainFromUrl(url: string) {
  try {
    const domain = new URL(url).hostname
    return domain.replace('www.', '')
  } catch {
    return url
  }
}
</script>

<template>
  <div v-if="sources?.length" class="mt-3 border-t border-surface-200 pt-3">
    <!-- Header -->
    <button
      @click="expanded = !expanded"
      class="flex items-center gap-2 text-xs text-surface-600 hover:text-surface-800 transition-colors w-full"
    >
      <Globe class="w-3.5 h-3.5 text-blue-500" />
      <span class="font-medium">Nguồn từ web ({{ sources.length }})</span>
      <ChevronUp v-if="expanded" class="w-3 h-3 ml-auto" />
      <ChevronDown v-else class="w-3 h-3 ml-auto" />
    </button>
    
    <!-- Sources List -->
    <div v-show="expanded" class="mt-2 space-y-2">
      <a
        v-for="(source, index) in sources"
        :key="index"
        :href="source.url"
        target="_blank"
        rel="noopener noreferrer"
        class="block p-2.5 bg-blue-50/50 hover:bg-blue-50 border border-blue-100 rounded-lg transition-colors group"
      >
        <div class="flex items-start gap-2">
          <div class="flex-1 min-w-0">
            <!-- Title -->
            <p class="text-sm font-medium text-surface-800 group-hover:text-blue-700 line-clamp-1">
              {{ source.title || 'Untitled' }}
            </p>
            
            <!-- Domain -->
            <p class="text-xs text-blue-600 mt-0.5 flex items-center gap-1">
              <Globe class="w-3 h-3" />
              {{ getDomainFromUrl(source.url) }}
            </p>
            
            <!-- Content Preview -->
            <p v-if="source.content" class="text-xs text-surface-600 mt-1 line-clamp-2">
              {{ truncateContent(source.content) }}
            </p>
          </div>
          
          <!-- External Link Icon -->
          <ExternalLink class="w-4 h-4 text-surface-400 group-hover:text-blue-500 flex-shrink-0" />
        </div>
      </a>
    </div>
    
    <!-- Note about web search -->
    <p class="text-xs text-surface-400 mt-2 italic">
      💡 Thông tin bổ sung được tìm kiếm tự động từ web để hỗ trợ câu trả lời.
    </p>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
