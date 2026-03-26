import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, summaryApi } from '@/services/api'
import type { WebSource, Citation } from '@/types'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    document_id: string
    filename: string
    chunk_index: number
    text_preview: string
    relevance_score: number
  }>
  citations?: Citation[]
  webSources?: WebSource[]
  timestamp: Date
}

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const currentNotebookId = ref<string | null>(null)

  // Actions
  function setNotebook(notebookId: string) {
    if (currentNotebookId.value !== notebookId) {
      currentNotebookId.value = notebookId
      messages.value = []
    }
  }

  async function sendMessage(content: string, enableWebSearch: boolean = false) {
    if (!currentNotebookId.value) return

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    messages.value.push(userMessage)

    isLoading.value = true

    try {
      // Build chat history
      const chatHistory = messages.value
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))

      const response = await chatApi.send({
        message: content,
        notebook_id: currentNotebookId.value,
        chat_history: chatHistory.slice(0, -1), // Exclude current message
        enable_web_search: enableWebSearch
      })

      // Debug: Log API response
      console.log('[ChatStore] API response.data:', response.data)
      console.log('[ChatStore] Citations from API:', response.data.citations)
      console.log('[ChatStore] Citations length:', response.data.citations?.length || 0)

      // Add assistant message
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.data.message,
        sources: response.data.sources,
        citations: response.data.citations,
        webSources: response.data.web_sources,
        timestamp: new Date()
      }

      console.log('[ChatStore] Assistant message created:', assistantMessage)
      console.log('[ChatStore] Message citations:', assistantMessage.citations)

      messages.value.push(assistantMessage)

      return assistantMessage
    } catch (error: any) {
      // Add error message
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Xin lỗi, đã có lỗi xảy ra: ${error.message || 'Unknown error'}`,
        timestamp: new Date()
      }
      messages.value.push(errorMessage)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function generateSummary(style: 'brief' | 'detailed' | 'bullet_points' = 'detailed') {
    if (!currentNotebookId.value) return

    isLoading.value = true

    try {
      const response = await summaryApi.generate({
        notebook_id: currentNotebookId.value,
        style
      })

      // Add summary as assistant message
      const summaryMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `📝 **Tóm tắt (${style}):**\n\n${response.data.summary}`,
        timestamp: new Date()
      }
      messages.value.push(summaryMessage)

      return summaryMessage
    } catch (error: any) {
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    isLoading,
    currentNotebookId,
    setNotebook,
    sendMessage,
    generateSummary,
    clearMessages
  }
})
