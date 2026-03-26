<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { X, Check, Tag, Loader2 } from 'lucide-vue-next'
import { categoriesApi } from '@/services/api'
import type { CategoryInfo, CategoryAssignment } from '@/types'

const props = defineProps<{
  isOpen: boolean
  documentId: string
  documentName: string
  currentCategories: CategoryAssignment[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', categories: string[]): void
}>()

const allCategories = ref<CategoryInfo[]>([])
const selectedCategories = ref<string[]>([])
const loading = ref(false)
const saving = ref(false)

// Group categories by type
const groupedCategories = computed(() => {
  const acm = allCategories.value.filter(c => c.type === 'ACM')
  const extended = allCategories.value.filter(c => c.type === 'Extended')
  return { acm, extended }
})

async function fetchCategories() {
  loading.value = true
  try {
    const response = await categoriesApi.list()
    allCategories.value = response.data.categories
  } catch (e) {
    console.error('Failed to fetch categories:', e)
  } finally {
    loading.value = false
  }
}

function toggleCategory(categoryName: string) {
  const idx = selectedCategories.value.indexOf(categoryName)
  if (idx === -1) {
    // Max 3 categories
    if (selectedCategories.value.length < 3) {
      selectedCategories.value.push(categoryName)
    }
  } else {
    selectedCategories.value.splice(idx, 1)
  }
}

function isSelected(categoryName: string) {
  return selectedCategories.value.includes(categoryName)
}

function getOriginalCategory(categoryName: string) {
  return props.currentCategories.find(c => c.category === categoryName)
}

async function handleSave() {
  saving.value = true
  try {
    await categoriesApi.updateDocument(props.documentId, selectedCategories.value)
    emit('save', selectedCategories.value)
    emit('close')
  } catch (e) {
    console.error('Failed to update categories:', e)
    alert('Không thể cập nhật phân loại. Vui lòng thử lại.')
  } finally {
    saving.value = false
  }
}

// Initialize selected categories from current
watch(() => props.isOpen, (open) => {
  if (open) {
    selectedCategories.value = props.currentCategories.map(c => c.category)
    if (allCategories.value.length === 0) {
      fetchCategories()
    }
  }
}, { immediate: true })

onMounted(() => {
  fetchCategories()
})
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      @click.self="emit('close')"
    >
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] flex flex-col animate-scale-in">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-surface-200">
          <div>
            <h3 class="font-semibold text-surface-800">Phân loại tài liệu</h3>
            <p class="text-sm text-surface-500 truncate max-w-xs">{{ documentName }}</p>
          </div>
          <button 
            @click="emit('close')"
            class="p-2 hover:bg-surface-100 rounded-lg transition-colors"
          >
            <X class="w-5 h-5 text-surface-500" />
          </button>
        </div>
        
        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="loading" class="flex items-center justify-center py-8">
            <Loader2 class="w-6 h-6 text-primary-500 animate-spin" />
          </div>
          
          <div v-else class="space-y-6">
            <!-- Info -->
            <div class="text-sm text-surface-600 bg-blue-50 rounded-lg p-3">
              <Tag class="w-4 h-4 inline mr-1" />
              Chọn tối đa 3 phân loại phù hợp với nội dung tài liệu.
              <span class="font-medium">({{ selectedCategories.length }}/3)</span>
            </div>
            
            <!-- ACM Categories -->
            <div>
              <h4 class="text-sm font-semibold text-surface-700 mb-2 flex items-center gap-2">
                <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                ACM Computing Classification
              </h4>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="cat in groupedCategories.acm"
                  :key="cat.name"
                  @click="toggleCategory(cat.name)"
                  class="text-left p-2 rounded-lg border transition-all text-sm"
                  :class="isSelected(cat.name)
                    ? 'bg-blue-50 border-blue-300 text-blue-700'
                    : 'border-surface-200 hover:bg-surface-50 text-surface-700'"
                >
                  <div class="flex items-center gap-2">
                    <Check 
                      v-if="isSelected(cat.name)" 
                      class="w-4 h-4 text-blue-500 flex-shrink-0" 
                    />
                    <span class="truncate">{{ cat.name }}</span>
                  </div>
                  <!-- Show original confidence if was auto-assigned -->
                  <span 
                    v-if="getOriginalCategory(cat.name)?.is_auto"
                    class="text-xs text-surface-400 ml-6"
                  >
                    (AI: {{ getOriginalCategory(cat.name)?.confidence }})
                  </span>
                </button>
              </div>
            </div>
            
            <!-- Extended Categories -->
            <div>
              <h4 class="text-sm font-semibold text-surface-700 mb-2 flex items-center gap-2">
                <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                Extended Categories
              </h4>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="cat in groupedCategories.extended"
                  :key="cat.name"
                  @click="toggleCategory(cat.name)"
                  class="text-left p-2 rounded-lg border transition-all text-sm"
                  :class="isSelected(cat.name)
                    ? 'bg-green-50 border-green-300 text-green-700'
                    : 'border-surface-200 hover:bg-surface-50 text-surface-700'"
                >
                  <div class="flex items-center gap-2">
                    <Check 
                      v-if="isSelected(cat.name)" 
                      class="w-4 h-4 text-green-500 flex-shrink-0" 
                    />
                    <span class="truncate">{{ cat.name }}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 p-4 border-t border-surface-200">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-surface-600 hover:bg-surface-100 rounded-lg transition-colors"
          >
            Hủy
          </button>
          <button
            @click="handleSave"
            :disabled="saving"
            class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
            <Check v-else class="w-4 h-4" />
            Lưu thay đổi
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes scale-in {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.animate-scale-in {
  animation: scale-in 0.2s ease-out;
}
</style>
