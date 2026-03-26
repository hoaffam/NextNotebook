import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

interface User {
  id: string
  email: string
  username: string
  full_name?: string
  created_at: string
}

interface RegisterData {
  email: string
  password: string
  username: string
  full_name?: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)

  // Initialize from localStorage
  const savedToken = localStorage.getItem('token')
  const savedUser = localStorage.getItem('user')
  if (savedToken) {
    token.value = savedToken
    api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
  }
  if (savedUser) {
    try {
      user.value = JSON.parse(savedUser)
    } catch (e) {
      localStorage.removeItem('user')
    }
  }

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const login = async (email: string, password: string) => {
    loading.value = true
    try {
      const response = await api.post('/auth/login', { email, password })
      const data = response.data

      token.value = data.access_token
      user.value = data.user

      // Save to localStorage
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))

      // Set auth header
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

      return data
    } finally {
      loading.value = false
    }
  }

  const register = async (userData: RegisterData) => {
    loading.value = true
    try {
      const response = await api.post('/auth/register', userData)
      const data = response.data

      token.value = data.access_token
      user.value = data.user

      // Save to localStorage
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))

      // Set auth header
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

      return data
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete api.defaults.headers.common['Authorization']
  }

  const checkAuth = async () => {
    if (!token.value) return false

    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    checkAuth
  }
})
