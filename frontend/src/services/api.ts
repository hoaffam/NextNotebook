import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect if already on auth page or if it's an auth request
      const isAuthRequest = error.config?.url?.includes('/auth/')
      const isOnAuthPage = window.location.pathname === '/auth'
      
      if (!isAuthRequest && !isOnAuthPage) {
        // Token expired or invalid
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  }
)

// ==================== Notebooks ====================
export const notebooksApi = {
  list: () => api.get('/notebooks/'),
  get: (id: string) => api.get(`/notebooks/${id}`),
  create: (data: { name: string; description?: string }) => 
    api.post('/notebooks/', data),
  update: (id: string, data: { name?: string; description?: string }) => 
    api.put(`/notebooks/${id}`, data),
  delete: (id: string) => api.delete(`/notebooks/${id}`),
  getOverview: (id: string, forceRefresh = false) => 
    api.get(`/notebooks/${id}/overview`, { params: { force_refresh: forceRefresh } })
}

// ==================== Documents ====================
export const documentsApi = {
  upload: (notebookId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('notebook_id', notebookId)
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  listByNotebook: (notebookId: string) => 
    api.get(`/documents/notebook/${notebookId}`),
  delete: (id: string) => api.delete(`/documents/${id}`)
}

// ==================== Categories ====================
export const categoriesApi = {
  list: () => api.get('/categories/'),
  updateDocument: (documentId: string, categories: string[]) =>
    api.put('/categories/document', { document_id: documentId, categories }),
  filterByCategory: (notebookId: string, categories: string[], includeUncategorized = true) =>
    api.post('/categories/filter', { 
      notebook_id: notebookId, 
      categories, 
      include_uncategorized: includeUncategorized 
    }),
  getStats: (notebookId: string) => api.get(`/categories/notebook/${notebookId}/stats`)
}

// ==================== Chat ====================
export const chatApi = {
  send: (data: { 
    message: string; 
    notebook_id: string; 
    chat_history?: Array<{ role: string; content: string }>;
    enable_web_search?: boolean
  }) => api.post('/chat/', data)
}

// ==================== Summary ====================
export const summaryApi = {
  generate: (data: { 
    notebook_id: string; 
    style?: 'brief' | 'detailed' | 'bullet_points';
    max_length?: number 
  }) => api.post('/summary/', data),
  
  document: (documentId: string, style?: string) => 
    api.post(`/summary/document/${documentId}`, null, { params: { style } })
}

// ==================== Quiz ====================
export const quizApi = {
  generate: (data: { 
    notebook_id: string; 
    num_questions?: number; 
    difficulty?: 'easy' | 'medium' | 'hard' 
  }) => api.post('/quiz/generate/', data),
  
  get: (id: string) => api.get(`/quiz/${id}`),
  
  delete: (id: string) => api.delete(`/quiz/${id}`),
  
  submit: (quizId: string, answers: Record<string, string>) => 
    api.post(`/quiz/${quizId}/submit`, { answers }),
  
  listByNotebook: (notebookId: string) => 
    api.get(`/quiz/notebook/${notebookId}`)
}

export default api
