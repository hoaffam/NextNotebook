<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotebookStore } from '@/stores/notebook'
import { useAuthStore } from '@/stores/auth'
import { 
  Plus, 
  BookOpen, 
  Trash2, 
  Clock,
  FileText,
  LogOut,
  User
} from 'lucide-vue-next'

const router = useRouter()
const store = useNotebookStore()
const authStore = useAuthStore()

const showCreateModal = ref(false)
const showUserMenu = ref(false)
const newNotebookName = ref('')
const newNotebookDescription = ref('')

onMounted(() => {
  store.fetchNotebooks()
})

async function createNotebook() {
  if (!newNotebookName.value.trim()) return
  
  try {
    const notebook = await store.createNotebook(
      newNotebookName.value,
      newNotebookDescription.value
    )
    showCreateModal.value = false
    newNotebookName.value = ''
    newNotebookDescription.value = ''
    router.push(`/notebook/${notebook.id}`)
  } catch (error) {
    console.error('Failed to create notebook:', error)
  }
}

async function deleteNotebook(id: string, event: Event) {
  event.stopPropagation()
  if (confirm('Bạn có chắc muốn xóa notebook này?')) {
    await store.deleteNotebook(id)
  }
}

function openNotebook(id: string) {
  router.push(`/notebook/${id}`)
}

function logout() {
  authStore.logout()
  router.push('/auth')
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)
  
  if (hours < 1) return 'Vừa xong'
  if (hours < 24) return `${hours} giờ trước`
  if (days < 7) return `${days} ngày trước`
  return date.toLocaleDateString('vi-VN')
}
</script>

<template>
  <div class="min-h-screen bg-surface-50 bg-gradient-mesh">
    <!-- Header -->
    <header class="glass sticky top-0 z-10 border-b border-surface-200/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25 animate-float">
              <BookOpen class="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">NotebookLM</h1>
              <p class="text-xs text-surface-500 hidden sm:block">AI-powered document analysis</p>
            </div>
          </div>
          
          <div class="flex items-center gap-4">
            <button
              @click="showCreateModal = true"
              class="btn-primary flex items-center gap-2 px-5 py-2.5"
            >
              <Plus class="w-5 h-5" />
              <span class="hidden sm:inline">Tạo Notebook</span>
            </button>
            
            <!-- User Menu -->
            <div class="relative">
              <button
                @click="showUserMenu = !showUserMenu"
                class="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white/50 transition-all duration-200"
              >
                <div class="w-9 h-9 bg-gradient-to-br from-primary-400 to-accent-400 rounded-full flex items-center justify-center shadow-md">
                  <User class="w-4 h-4 text-white" />
                </div>
                <span class="text-sm font-medium text-surface-700 hidden sm:block">{{ authStore.user?.username }}</span>
              </button>
              
              <!-- Dropdown -->
              <Transition
                enter-active-class="transition duration-200 ease-out"
                enter-from-class="transform scale-95 opacity-0"
                enter-to-class="transform scale-100 opacity-100"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="transform scale-100 opacity-100"
                leave-to-class="transform scale-95 opacity-0"
              >
                <div 
                  v-if="showUserMenu"
                  class="absolute right-0 mt-2 w-56 glass rounded-2xl shadow-xl border border-surface-200/50 py-2 z-20"
                >
                  <div class="px-4 py-3 border-b border-surface-200/50">
                    <p class="text-sm font-semibold text-surface-800">{{ authStore.user?.full_name || authStore.user?.username }}</p>
                    <p class="text-xs text-surface-500 truncate">{{ authStore.user?.email }}</p>
                  </div>
                  <button
                    @click="logout"
                    class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50/50 transition-colors"
                  >
                    <LogOut class="w-4 h-4" />
                    <span>Đăng xuất</span>
                  </button>
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading -->
      <div v-if="store.loading" class="flex flex-col items-center justify-center py-20">
        <div class="relative w-16 h-16">
          <div class="absolute inset-0 rounded-full border-4 border-primary-200"></div>
          <div class="absolute inset-0 rounded-full border-4 border-primary-500 border-t-transparent animate-spin"></div>
        </div>
        <p class="mt-4 text-surface-500">Đang tải...</p>
      </div>

      <!-- Empty State -->
      <div 
        v-else-if="store.notebooks.length === 0" 
        class="text-center py-20 animate-fade-in"
      >
        <div class="w-24 h-24 bg-gradient-to-br from-primary-100 to-accent-100 rounded-3xl flex items-center justify-center mx-auto mb-6 animate-float">
          <BookOpen class="w-12 h-12 text-primary-500" />
        </div>
        <h2 class="text-2xl font-bold text-surface-800 mb-2">Chưa có notebook nào</h2>
        <p class="text-surface-500 mb-8 max-w-md mx-auto">Tạo notebook đầu tiên để bắt đầu tóm tắt và phân tích tài liệu với AI</p>
        <button
          @click="showCreateModal = true"
          class="btn-primary inline-flex items-center gap-2 px-8 py-3 text-lg"
        >
          <Plus class="w-6 h-6" />
          <span>Tạo Notebook</span>
        </button>
      </div>

      <!-- Notebooks Grid -->
      <div v-else>
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-surface-800">Notebooks của bạn</h2>
          <span class="text-sm text-surface-500">{{ store.notebooks.length }} notebooks</span>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="(notebook, index) in store.notebooks"
            :key="notebook.id"
            @click="openNotebook(notebook.id)"
            class="card-glow card-interactive p-6 animate-fade-in"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="w-14 h-14 bg-gradient-to-br from-primary-400 to-accent-400 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/20">
                <BookOpen class="w-7 h-7 text-white" />
              </div>
              <button
                @click="deleteNotebook(notebook.id, $event)"
                class="opacity-0 group-hover:opacity-100 p-2.5 text-surface-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all duration-200"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
            
            <h3 class="font-semibold text-surface-800 mb-2 text-lg line-clamp-1">
              {{ notebook.name }}
            </h3>
            
            <p v-if="notebook.description" class="text-sm text-surface-500 mb-4 line-clamp-2">
              {{ notebook.description }}
            </p>
            
            <div class="flex items-center gap-4 text-sm">
              <div class="flex items-center gap-1.5 px-3 py-1.5 bg-primary-50 text-primary-600 rounded-full">
                <FileText class="w-3.5 h-3.5" />
                <span class="font-medium">{{ notebook.sources_count }} nguồn</span>
              </div>
              <div class="flex items-center gap-1.5 text-surface-400">
                <Clock class="w-3.5 h-3.5" />
                <span>{{ formatDate(notebook.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Create Modal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div 
          v-if="showCreateModal"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          @click.self="showCreateModal = false"
        >
          <div class="glass bg-white rounded-3xl w-full max-w-md p-8 animate-scale-in shadow-2xl">
            <div class="text-center mb-6">
              <div class="w-16 h-16 bg-gradient-to-br from-primary-400 to-accent-400 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                <Plus class="w-8 h-8 text-white" />
              </div>
              <h2 class="text-2xl font-bold text-surface-800">Tạo Notebook Mới</h2>
              <p class="text-surface-500 mt-1">Bắt đầu phân tích tài liệu của bạn</p>
            </div>
            
            <div class="space-y-5">
              <div>
                <label class="block text-sm font-semibold text-surface-700 mb-2">
                  Tên Notebook *
                </label>
                <input
                  v-model="newNotebookName"
                  type="text"
                  placeholder="Ví dụ: Nghiên cứu AI"
                  class="input-modern"
                  @keyup.enter="createNotebook"
                />
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-surface-700 mb-2">
                  Mô tả (tùy chọn)
                </label>
                <textarea
                  v-model="newNotebookDescription"
                  rows="3"
                  placeholder="Mô tả ngắn về notebook..."
                  class="input-modern resize-none"
                ></textarea>
              </div>
            </div>
            
            <div class="flex gap-3 mt-8">
              <button
                @click="showCreateModal = false"
                class="btn-secondary flex-1 px-4 py-3"
              >
                Hủy
              </button>
              <button
                @click="createNotebook"
                :disabled="!newNotebookName.trim()"
                class="btn-primary flex-1 px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Tạo Notebook
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
