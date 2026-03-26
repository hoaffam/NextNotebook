import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notebooksApi, documentsApi } from '@/services/api'
import type { CategoryAssignment } from '@/types'

export interface Notebook {
  id: string
  name: string
  description?: string
  sources_count: number
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  filename: string
  notebook_id: string
  chunks_count: number
  status: string
  summary?: string
  key_topics?: string[]
  categories?: CategoryAssignment[]
}

export const useNotebookStore = defineStore('notebook', () => {
  // State
  const notebooks = ref<Notebook[]>([])
  const currentNotebook = ref<Notebook | null>(null)
  const documents = ref<Document[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const notebookCount = computed(() => notebooks.value.length)
  const currentDocuments = computed(() => documents.value)

  // Actions
  async function fetchNotebooks() {
    loading.value = true
    error.value = null
    try {
      const response = await notebooksApi.list()
      notebooks.value = response.data.notebooks
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch notebooks'
    } finally {
      loading.value = false
    }
  }

  async function fetchNotebook(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await notebooksApi.get(id)
      currentNotebook.value = response.data
      await fetchDocuments(id)
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch notebook'
    } finally {
      loading.value = false
    }
  }

  async function createNotebook(name: string, description?: string) {
    loading.value = true
    error.value = null
    try {
      const response = await notebooksApi.create({ name, description })
      notebooks.value.push(response.data)
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to create notebook'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteNotebook(id: string) {
    loading.value = true
    error.value = null
    try {
      await notebooksApi.delete(id)
      notebooks.value = notebooks.value.filter(n => n.id !== id)
    } catch (e: any) {
      error.value = e.message || 'Failed to delete notebook'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchDocuments(notebookId: string) {
    try {
      const response = await documentsApi.listByNotebook(notebookId)
      documents.value = response.data.documents
    } catch (e: any) {
      console.error('Failed to fetch documents:', e)
    }
  }

  async function uploadDocument(notebookId: string, file: File) {
    loading.value = true
    error.value = null
    try {
      const response = await documentsApi.upload(notebookId, file)
      documents.value.push(response.data)
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to upload document'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteDocument(id: string) {
    try {
      await documentsApi.delete(id)
      documents.value = documents.value.filter(d => d.id !== id)
    } catch (e: any) {
      console.error('Failed to delete document:', e)
      throw e
    }
  }

  return {
    // State
    notebooks,
    currentNotebook,
    documents,
    loading,
    error,
    // Getters
    notebookCount,
    currentDocuments,
    // Actions
    fetchNotebooks,
    fetchNotebook,
    createNotebook,
    deleteNotebook,
    fetchDocuments,
    uploadDocument,
    deleteDocument
  }
})
