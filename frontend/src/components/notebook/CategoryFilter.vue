<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Filter, X, ChevronDown } from 'lucide-vue-next'
import { categoriesApi } from '@/services/api'
import type { CategoryInfo } from '@/types'

const props = defineProps<{
  modelValue: string[]
  notebookId: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
  (e: 'filter-change', categories: string[]): void
}>()

const categories = ref<CategoryInfo[]>([])
const categoryStats = ref<Record<string, number>>({})
const loading = ref(false)
const isOpen = ref(false)

const selectedCategories = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const hasFilters = computed(() => selectedCategories.value.length > 0)

async function fetchCategories() {
  try {
    const response = await categoriesApi.list()
    categories.value = response.data.categories
  } catch (e) {
    console.error('Failed to fetch categories:', e)
  }
}

async function fetchStats() {
  if (!props.notebookId) return
  try {
    const response = await categoriesApi.getStats(props.notebookId)
    categoryStats.value = {}
    for (const stat of response.data.categories) {
      categoryStats.value[stat.category] = stat.count
    }
  } catch (e) {
    console.error('Failed to fetch category stats:', e)
  }
}

function toggleCategory(categoryName: string) {
  const current = [...selectedCategories.value]
  const index = current.indexOf(categoryName)
  
  if (index === -1) {
    current.push(categoryName)
  } else {
    current.splice(index, 1)
  }
  
  selectedCategories.value = current
  emit('filter-change', current)
}

function clearFilters() {
  selectedCategories.value = []
  emit('filter-change', [])
}

function getCategoryTypeColor(type: string) {
  switch (type) {
    case 'ACM': return 'border-l-blue-400'
    case 'Extended': return 'border-l-green-400'
    default: return 'border-l-gray-400'
  }
}

onMounted(() => {
  fetchCategories()
  fetchStats()
})

// Expose refresh method
defineExpose({ 
  refresh: () => {
    fetchCategories()
    fetchStats()
  }
})
</script>

<template>
  <div class="relative">
    <!-- Filter Button -->
    <button
      @click="isOpen = !isOpen"
      class="flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors"
      :class="hasFilters 
        ? 'bg-primary-50 border-primary-200 text-primary-700' 
        : 'bg-white border-surface-200 text-surface-700 hover:bg-surface-50'"
    >
      <Filter class="w-4 h-4" />
      <span class="text-sm">
        {{ hasFilters ? `${selectedCategories.length} bộ lọc` : 'Lọc theo danh mục' }}
      </span>
      <ChevronDown 
        class="w-4 h-4 transition-transform" 
        :class="isOpen ? 'rotate-180' : ''"
      />
    </button>
    
    <!-- Selected Filters Preview -->
    <div v-if="hasFilters && !isOpen" class="flex flex-wrap gap-1 mt-2">
      <span
        v-for="cat in selectedCategories.slice(0, 3)"
        :key="cat"
        class="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full text-xs"
      >
        {{ cat.length > 15 ? cat.substring(0, 15) + '...' : cat }}
        <button @click.stop="toggleCategory(cat)" class="hover:text-primary-900">
          <X class="w-3 h-3" />
        </button>
      </span>
      <span v-if="selectedCategories.length > 3" class="text-xs text-surface-500">
        +{{ selectedCategories.length - 3 }} khác
      </span>
    </div>
    
    <!-- Dropdown -->
    <div
      v-if="isOpen"
      class="absolute top-full left-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white border border-surface-200 rounded-xl shadow-lg z-50"
    >
      <!-- Header -->
      <div class="sticky top-0 bg-white border-b border-surface-100 px-4 py-3 flex items-center justify-between">
        <span class="font-medium text-surface-800">Danh mục</span>
        <button
          v-if="hasFilters"
          @click="clearFilters"
          class="text-xs text-primary-600 hover:text-primary-700"
        >
          Xóa tất cả
        </button>
      </div>
      
      <!-- Categories List -->
      <div class="p-2">
        <!-- ACM Categories -->
        <div class="mb-2">
          <p class="text-xs text-surface-500 px-2 py-1 font-medium">ACM Computing</p>
          <div class="space-y-0.5">
            <button
              v-for="cat in categories.filter(c => c.type === 'ACM')"
              :key="cat.name"
              @click="toggleCategory(cat.name)"
              class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors border-l-2"
              :class="[
                getCategoryTypeColor(cat.type),
                selectedCategories.includes(cat.name)
                  ? 'bg-primary-50 text-primary-700'
                  : 'hover:bg-surface-50 text-surface-700'
              ]"
            >
              <span class="flex-1 truncate">{{ cat.name }}</span>
              <span 
                v-if="categoryStats[cat.name]" 
                class="text-xs px-1.5 py-0.5 rounded-full"
                :class="selectedCategories.includes(cat.name)
                  ? 'bg-primary-200 text-primary-700'
                  : 'bg-surface-100 text-surface-500'"
              >
                {{ categoryStats[cat.name] }}
              </span>
            </button>
          </div>
        </div>
        
        <!-- Extended Categories -->
        <div>
          <p class="text-xs text-surface-500 px-2 py-1 font-medium">Mở rộng</p>
          <div class="space-y-0.5">
            <button
              v-for="cat in categories.filter(c => c.type === 'Extended')"
              :key="cat.name"
              @click="toggleCategory(cat.name)"
              class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors border-l-2"
              :class="[
                getCategoryTypeColor(cat.type),
                selectedCategories.includes(cat.name)
                  ? 'bg-primary-50 text-primary-700'
                  : 'hover:bg-surface-50 text-surface-700'
              ]"
            >
              <span class="flex-1 truncate">{{ cat.name }}</span>
              <span 
                v-if="categoryStats[cat.name]" 
                class="text-xs px-1.5 py-0.5 rounded-full"
                :class="selectedCategories.includes(cat.name)
                  ? 'bg-primary-200 text-primary-700'
                  : 'bg-surface-100 text-surface-500'"
              >
                {{ categoryStats[cat.name] }}
              </span>
            </button>
          </div>
        </div>
        
        <!-- Uncategorized -->
        <button
          @click="toggleCategory('Uncategorized')"
          class="w-full flex items-center gap-2 px-3 py-2 mt-2 rounded-lg text-left text-sm transition-colors border-l-2 border-l-gray-300"
          :class="selectedCategories.includes('Uncategorized')
            ? 'bg-primary-50 text-primary-700'
            : 'hover:bg-surface-50 text-surface-700'"
        >
          <span class="flex-1">Uncategorized</span>
          <span 
            v-if="categoryStats['Uncategorized']" 
            class="text-xs px-1.5 py-0.5 rounded-full"
            :class="selectedCategories.includes('Uncategorized')
              ? 'bg-primary-200 text-primary-700'
              : 'bg-surface-100 text-surface-500'"
          >
            {{ categoryStats['Uncategorized'] }}
          </span>
        </button>
      </div>
    </div>
    
    <!-- Backdrop -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40"
      @click="isOpen = false"
    />
  </div>
</template>
