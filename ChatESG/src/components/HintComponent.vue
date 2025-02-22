<!-- 提示組件 (HintComponent.vue) -->
<template>
  <div class="hint-container">
    <!-- 提示按鈕 -->
    <button 
      v-if="!loading && (hintText || canGenerateHint)"
      class="hint-button"
      @click="toggleHint"
      :aria-label="showHint ? '關閉提示' : '顯示提示'"
      :class="{ 'active': showHint }"
    >
      <i class="mdi" :class="[
        showHint ? 'mdi-chevron-up' : 'mdi-chevron-down',
        { 'has-hint': hintText }
      ]"></i>
      <span class="hint-label">填寫建議</span>
      <i class="mdi mdi-lightbulb-on-outline hint-icon" :class="{ 'has-hint': hintText }"></i>
    </button>

    <!-- 提示內容區域 -->
    <transition name="slide">
      <div v-if="showHint" class="hint-content" :class="{ 'dark': isDarkMode }">
        <div class="hint-header">
          <span class="hint-title">
            <i class="mdi mdi-lightbulb-on"></i>
            填寫建議
          </span>
          <button class="close-button" @click="toggleHint">
            <i class="mdi mdi-close"></i>
          </button>
        </div>
        
        <div class="hint-body">
          <div v-if="loading" class="loading-state">
            <i class="mdi mdi-loading mdi-spin"></i>
            <span>正在載入提示...</span>
          </div>
          
          <div v-else-if="error" class="error-state">
            <i class="mdi mdi-alert"></i>
            <span>{{ error }}</span>
            <button class="retry-button" @click="retryLoadHint">
              重試
            </button>
          </div>
          
          <div v-else-if="hintText" class="hint-text">
            <div class="hint-text-content">
              {{ hintText }}
            </div>
          </div>
          
          <div v-else-if="canGenerateHint" class="generate-hint">
            <button class="generate-button" @click="generateHint" :disabled="generating">
              <i class="mdi" :class="generating ? 'mdi-loading mdi-spin' : 'mdi-auto-fix'"></i>
              <span>{{ generating ? '正在生成提示...' : '自動生成提示' }}</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useCompanyInfoStore } from '@/stores/companyInfo'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  isDarkMode: {
    type: Boolean,
    default: false
  }
})

// 狀態管理
const showHint = ref(false)
const hintText = ref('')
const loading = ref(false)
const error = ref('')
const generating = ref(false)
const canGenerateHint = ref(true)

const companyInfoStore = useCompanyInfoStore()

// 監聽標題變化
watch(() => props.title, async (newTitle) => {
  if (newTitle && showHint.value) {
    await loadHint()
  }
}, { immediate: true })

// 切換提示顯示狀態
const toggleHint = () => {
  showHint.value = !showHint.value
  if (showHint.value && props.title) {
    loadHint()
  }
}

// 載入提示
const loadHint = async () => {
  if (!props.title) return
  
  loading.value = true
  error.value = ''
  
  try {
    const hint = await companyInfoStore.fetchHint(props.title)
    hintText.value = hint
    canGenerateHint.value = !hintText.value
  } catch (err) {
    error.value = '載入提示失敗，請稍後再試'
    console.error('載入提示失敗:', err)
  } finally {
    loading.value = false
  }
}

// 重試載入提示
const retryLoadHint = () => {
  loadHint()
}

// 生成提示
const generateHint = async () => {
  if (!props.title || generating.value) return
  
  generating.value = true
  error.value = ''
  
  try {
    const hint = await companyInfoStore.generateHint(props.title)
    hintText.value = hint
    canGenerateHint.value = false
  } catch (err) {
    error.value = '生成提示失敗，請稍後再試'
    console.error('生成提示失敗:', err)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.hint-container {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.hint-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  background: none;
  border: none;
  border-top: 1px solid #e2e8f0;
  padding: 8px 16px;
  cursor: pointer;
  color: #4b5563;
  font-size: 14px;
  transition: all 0.2s ease;
}

.dark .hint-button {
  border-top-color: #2d2d2d;
}

.hint-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.hint-button.active {
  background-color: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}

.dark .hint-button {
  color: #e2e8f0;
}

.dark .hint-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.dark .hint-button.active {
  background-color: rgba(96, 165, 250, 0.1);
  color: #60a5fa;
}

.hint-button i {
  font-size: 16px;
}

.hint-icon {
  font-size: 18px !important;
}

.hint-button i.has-hint {
  color: #2563eb;
}

.dark .hint-button i.has-hint {
  color: #60a5fa;
}

.hint-label {
  font-weight: 500;
}

.hint-content {
  width: 100%;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.dark .hint-content {
  background-color: #1a1a1a;
  border-color: #2d2d2d;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.hint-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.02);
}

.dark .hint-header {
  border-bottom-color: #2d2d2d;
  background-color: rgba(255, 255, 255, 0.02);
}

.hint-title {
  font-weight: 500;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.hint-title i {
  color: #2563eb;
  font-size: 18px;
}

.dark .hint-title {
  color: #ffffff;
}

.dark .hint-title i {
  color: #60a5fa;
}

.close-button {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #4b5563;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .close-button {
  color: #e2e8f0;
}

.dark .close-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.hint-body {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.hint-text-content {
  white-space: pre-line;
  line-height: 1.6;
  color: #1a1a1a;
  font-size: 14px;
}

.dark .hint-text-content {
  color: #e2e8f0;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  text-align: center;
  color: #4b5563;
  font-size: 14px;
}

.dark .loading-state,
.dark .error-state {
  color: #e2e8f0;
}

.error-state {
  color: #dc2626;
}

.dark .error-state {
  color: #ef4444;
}

.retry-button {
  margin-top: 8px;
  padding: 6px 12px;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.retry-button:hover {
  background-color: #dc2626;
}

.generate-button {
  width: 100%;
  padding: 8px 16px;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
  font-size: 14px;
}

.generate-button:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.generate-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 過渡動畫 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 400px;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding: 0;
}

/* Loading 動畫 */
.mdi-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 滾動條樣式 */
.hint-body::-webkit-scrollbar {
  width: 6px;
}

.hint-body::-webkit-scrollbar-track {
  background: transparent;
}

.hint-body::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 3px;
}

.dark .hint-body::-webkit-scrollbar-thumb {
  background-color: #4a5568;
}
</style> 