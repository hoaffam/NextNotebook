import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/auth',
    name: 'auth',
    component: () => import('@/views/AuthView.vue'),
    meta: { title: 'Đăng nhập', requiresGuest: true }
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: 'Notebooks', requiresAuth: true }
  },
  {
    path: '/notebook/:id',
    name: 'notebook',
    component: () => import('@/views/NotebookView.vue'),
    meta: { title: 'Notebook', requiresAuth: true }
  },
  {
    path: '/quiz/:id',
    name: 'quiz',
    component: () => import('@/views/QuizView.vue'),
    meta: { title: 'Quiz', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  // Update page title
  document.title = `${to.meta.title || 'NotebookLM'} | NotebookLM Clone`
  
  // Check authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'auth' })
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
