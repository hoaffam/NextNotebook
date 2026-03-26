<script setup lang="ts">
import { computed, watchEffect, ref } from 'vue'
import { User, Bot, Copy, Check } from 'lucide-vue-next'
import type { WebSource, Citation } from '@/types'
import WebSourcesPanel from './WebSourcesPanel.vue'
import CitationsPanel from './CitationsPanel.vue'
import InlineCitationBadge from './InlineCitationBadge.vue'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  messageId?: string
  sources?: Array<{
    document_id: string
    filename: string
    chunk_index: number
    score?: number
  }>
  citations?: Citation[]
  webSources?: WebSource[]
  timestamp?: string
}>()

const copied = ref(false)
const forceOpenCitationId = ref<number | null>(null)
const idPrefix = computed(() => props.messageId ? `msg-${props.messageId}` : 'citation')

// Debug: Watch for citations changes
watchEffect(() => {
  if (props.role === 'assistant') {
    console.log('[MessageBubble] Citations prop:', props.citations)
    console.log('[MessageBubble] Citations length:', props.citations?.length || 0)
    console.log('[MessageBubble] Should show CitationsPanel:', props.citations?.length && props.role === 'assistant')
  }
})

type RenderSegment = { type: 'text'; html: string } | { type: 'citation'; id: number }

function formatText(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-surface-100 px-1 rounded">$1</code>')
    .replace(/\n/g, '<br>')
}

const renderedSegments = computed<RenderSegment[]>(() => {
  const segments: RenderSegment[] = []
  const regex = /\[cid:(\d+)\]/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  const content = props.content || ''

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index)
      segments.push({ type: 'text', html: formatText(text) })
    }
    segments.push({ type: 'citation', id: Number(match[1]) })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < content.length) {
    const text = content.slice(lastIndex)
    segments.push({ type: 'text', html: formatText(text) })
  }

  // If no citations present, return single text segment with formatting
  if (segments.length === 0) {
    segments.push({ type: 'text', html: formatText(content) })
  }

  return segments
})

function handleOpenCitation(id: number) {
  forceOpenCitationId.value = id
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch (e) {
    console.error('Copy failed:', e)
  }
}

function formatTime(timestamp: string) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div 
    class="group flex gap-3 animate-fade-in"
    :class="role === 'user' ? 'flex-row-reverse' : 'flex-row'"
  >
    <!-- Avatar -->
    <div 
      class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
      :class="role === 'user' ? 'bg-primary-100' : 'bg-surface-100'"
    >
      <User v-if="role === 'user'" class="w-4 h-4 text-primary-600" />
      <Bot v-else class="w-4 h-4 text-surface-600" />
    </div>
    
    <!-- Message Content -->
    <div class="flex flex-col max-w-[80%]" :class="role === 'user' ? 'items-end' : 'items-start'">
      <div
        class="px-4 py-3 rounded-2xl"
        :class="role === 'user'
          ? 'bg-primary-600 text-white rounded-br-md'
          : 'bg-white border border-surface-200 text-surface-800 rounded-bl-md shadow-sm'"
      >
        <div class="whitespace-pre-wrap citation-content">
          <template v-for="(segment, idx) in renderedSegments" :key="idx">
            <InlineCitationBadge
              v-if="segment.type === 'citation'"
              :citation-id="segment.id"
              :target-prefix="idPrefix"
              @open="handleOpenCitation"
            />
            <span v-else v-html="segment.html"></span>
          </template>
        </div>
        
        <!-- Sources -->
        <div 
          v-if="sources?.length && role === 'assistant'" 
          class="mt-3 pt-3 border-t"
          :class="role === 'user' ? 'border-primary-500' : 'border-surface-200'"
        >
          <p class="text-xs opacity-70 mb-2">📚 Nguồn tham khảo:</p>
          <div class="space-y-1">
            <div 
              v-for="source in sources.slice(0, 3)" 
              :key="source.document_id + source.chunk_index"
              class="text-xs rounded px-2 py-1"
              :class="role === 'user' ? 'bg-primary-500' : 'bg-surface-50'"
            >
              📄 {{ source.filename }}
              <span v-if="source.score" class="opacity-60">
                ({{ (source.score * 100).toFixed(0) }}%)
              </span>
            </div>
          </div>
        </div>

        <!-- Enhanced Citations Panel (NEW) -->
        <CitationsPanel
          v-if="citations?.length"
          :citations="citations"
          :id-prefix="idPrefix"
          :auto-open-id="forceOpenCitationId"
        />

        <!-- Web Sources (CRAG) -->
        <WebSourcesPanel
          v-if="webSources?.length && role === 'assistant'"
          :sources="webSources"
        />
      </div>
      
      <!-- Actions & Timestamp -->
      <div 
        class="flex items-center gap-2 mt-1 px-2"
        :class="role === 'user' ? 'flex-row-reverse' : 'flex-row'"
      >
        <span v-if="timestamp" class="text-xs text-surface-400">
          {{ formatTime(timestamp) }}
        </span>
        
        <button
          v-if="role === 'assistant'"
          @click="copyToClipboard"
          class="opacity-0 group-hover:opacity-100 p-1 hover:bg-surface-100 rounded transition-all"
          :title="copied ? 'Đã copy!' : 'Copy'"
        >
          <Check v-if="copied" class="w-3 h-3 text-green-500" />
          <Copy v-else class="w-3 h-3 text-surface-400" />
        </button>
      </div>
    </div>
  </div>
</template>
