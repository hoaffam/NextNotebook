<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import MessageBubble from './MessageBubble.vue'
import ChatInput from './ChatInput.vue'
import LoadingSpinner from '../common/LoadingSpinner.vue'
import type { WebSource, Citation } from '@/types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    document_id: string
    filename: string
    chunk_index: number
    score?: number
  }>
  citations?: Citation[]
  webSources?: WebSource[]
  timestamp: string
}

const props = defineProps<{
  messages: Message[]
  loading?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

const messagesContainer = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Auto scroll on new messages
watch(() => props.messages.length, () => {
  scrollToBottom()
})

onMounted(() => {
  scrollToBottom()
})

function handleSend(message: string) {
  emit('send', message)
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Messages Area -->
    <div 
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-6 space-y-6"
    >
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="text-center py-12">
        <div class="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Sparkles class="w-8 h-8 text-primary-600" />
        </div>
        <h2 class="text-xl font-semibold text-surface-800 mb-2">
          Xin chào! 👋
        </h2>
        <p class="text-surface-500 max-w-md mx-auto">
          Tôi là trợ lý AI của bạn. Hãy hỏi tôi bất cứ điều gì về tài liệu đã tải lên. 
          Gõ <code class="bg-surface-100 px-2 py-0.5 rounded">/help</code> để xem các lệnh có sẵn.
        </p>
      </div>
      
      <!-- Message List -->
      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :message-id="message.id"
        :role="message.role"
        :content="message.content"
        :sources="message.sources"
        :citations="message.citations"
        :web-sources="message.webSources"
        :timestamp="message.timestamp"
      />
      
      <!-- Typing Indicator -->
      <div v-if="loading" class="flex gap-3">
        <div class="w-8 h-8 rounded-full bg-surface-100 flex items-center justify-center">
          <Sparkles class="w-4 h-4 text-surface-500" />
        </div>
        <div class="bg-white border border-surface-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
          <div class="flex items-center gap-2">
            <span class="flex gap-1">
              <span class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </span>
            <span class="text-sm text-surface-500">Đang suy nghĩ...</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Input Area -->
    <div class="border-t border-surface-200 p-4 bg-white">
      <ChatInput
        :loading="loading"
        :disabled="disabled"
        @send="handleSend"
      />
    </div>
  </div>
</template>
