<script setup lang="ts">
import { ref, computed } from 'vue'
import { Send, Loader2, Paperclip, Mic, Sparkles } from 'lucide-vue-next'

const props = defineProps<{
  disabled?: boolean
  loading?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  send: [message: string]
  'command-select': [command: string]
}>()

const input = ref('')
const showCommands = ref(false)

const commands = [
  { value: '/summary', label: 'Tóm tắt', description: 'Tóm tắt nội dung tài liệu', icon: '📝' },
  { value: '/quiz', label: 'Tạo Quiz', description: 'Tạo câu hỏi trắc nghiệm', icon: '🎯' },
  { value: '/faq', label: 'FAQ', description: 'Sinh câu hỏi thường gặp', icon: '❓' },
  { value: '/help', label: 'Trợ giúp', description: 'Xem các lệnh có sẵn', icon: '💡' }
]

const filteredCommands = computed(() => {
  if (!input.value.startsWith('/')) return []
  const query = input.value.slice(1).toLowerCase()
  return commands.filter(cmd => 
    cmd.value.slice(1).includes(query) || cmd.label.toLowerCase().includes(query)
  )
})

function handleSend() {
  if (!input.value.trim() || props.loading) return
  emit('send', input.value.trim())
  input.value = ''
  showCommands.value = false
}

function selectCommand(command: string) {
  input.value = command + ' '
  showCommands.value = false
}

function handleInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  input.value = value
  showCommands.value = value.startsWith('/') && value.length > 0
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
  if (e.key === 'Escape') {
    showCommands.value = false
  }
}
</script>

<template>
  <div class="relative">
    <!-- Commands Dropdown -->
    <div 
      v-if="showCommands && filteredCommands.length > 0"
      class="absolute bottom-full left-0 right-0 mb-2 bg-white border border-surface-200 rounded-xl shadow-lg overflow-hidden"
    >
      <div class="p-2 border-b border-surface-100 text-xs text-surface-500">
        Lệnh có sẵn
      </div>
      <div class="max-h-48 overflow-y-auto">
        <button
          v-for="cmd in filteredCommands"
          :key="cmd.value"
          @click="selectCommand(cmd.value)"
          class="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-50 transition-colors text-left"
        >
          <span class="text-lg">{{ cmd.icon }}</span>
          <div>
            <p class="font-medium text-surface-800">{{ cmd.label }}</p>
            <p class="text-xs text-surface-500">{{ cmd.description }}</p>
          </div>
          <span class="ml-auto text-xs text-surface-400 font-mono">{{ cmd.value }}</span>
        </button>
      </div>
    </div>

    <!-- Input Area -->
    <div class="flex items-end gap-2 bg-white border border-surface-300 rounded-2xl p-2 focus-within:border-primary-400 focus-within:ring-2 focus-within:ring-primary-100 transition-all">
      <button
        class="p-2 text-surface-400 hover:text-surface-600 hover:bg-surface-100 rounded-xl transition-colors"
        title="Đính kèm file"
      >
        <Paperclip class="w-5 h-5" />
      </button>
      
      <textarea
        v-model="input"
        :placeholder="placeholder || 'Hỏi về tài liệu của bạn... (Gõ / để xem lệnh)'"
        :disabled="disabled || loading"
        @input="handleInput"
        @keydown="handleKeydown"
        rows="1"
        class="flex-1 resize-none outline-none text-surface-800 placeholder-surface-400 py-2 px-1 max-h-32 disabled:opacity-50"
      />
      
      <button
        class="p-2 text-surface-400 hover:text-surface-600 hover:bg-surface-100 rounded-xl transition-colors"
        title="Nhập giọng nói"
      >
        <Mic class="w-5 h-5" />
      </button>
      
      <button
        @click="handleSend"
        :disabled="!input.trim() || disabled || loading"
        class="p-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
        <Send v-else class="w-5 h-5" />
      </button>
    </div>
    
    <!-- Quick Actions -->
    <div class="flex items-center gap-2 mt-2 px-2">
      <button
        @click="input = '/summary'; showCommands = true"
        class="flex items-center gap-1 px-3 py-1.5 text-xs bg-surface-100 text-surface-600 rounded-full hover:bg-surface-200 transition-colors"
      >
        <Sparkles class="w-3 h-3" />
        Tóm tắt
      </button>
      <button
        @click="input = '/quiz'; showCommands = true"
        class="flex items-center gap-1 px-3 py-1.5 text-xs bg-surface-100 text-surface-600 rounded-full hover:bg-surface-200 transition-colors"
      >
        🎯 Quiz
      </button>
    </div>
  </div>
</template>
