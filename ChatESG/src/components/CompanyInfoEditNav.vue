<template>
  <nav :class="['nav-container', theme]">
    <div class="left-section">
      <button class="menu-btn" @click="toggleSidebar">
        <i class="mdi mdi-menu"></i>
      </button>
      <div class="file-info">
        <span class="file-name">{{ fileName }}</span>
      </div>
    </div>

    <div class="right-section">
      <div class="theme-toggle">
        <button @click="toggleTheme" class="theme-btn">
          <i :class="['mdi', theme === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny']"></i>
        </button>
      </div>

      <!-- 設定按鈕 -->
      <button class="settings-btn" @click="showSettings = true">
        <i class="mdi mdi-cog"></i>
      </button>

      <button class="save-btn" @click="saveContent" :class="{ 'saved': isSaved }">
        <i class="mdi mdi-content-save"></i>
        <span>{{ saveStatus }}</span>
      </button>
    </div>

    <!-- 設定對話框 -->
    <div v-if="showSettings" class="settings-modal">
      <div class="settings-content">
        <div class="settings-header">
          <h3>設定</h3>
          <button class="close-btn" @click="showSettings = false">
            <i class="mdi mdi-close"></i>
          </button>
        </div>
        
        <div class="settings-body">
          <div class="setting-item">
            <label>自動儲存間隔 (秒)</label>
            <input 
              type="number" 
              v-model="autoSaveInterval" 
              min="5" 
              max="300"
              @change="updateAutoSaveInterval"
            >
          </div>
          
          <div class="setting-item">
            <label>字體大小</label>
            <select v-model="fontSize" @change="updateFontSize">
              <option value="small">小</option>
              <option value="medium">中</option>
              <option value="large">大</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted, inject } from 'vue'

// 注入父組件提供的儲存方法
const handleSave = inject('handleSave')

// 基本狀態
const theme = ref('dark')
const fileName = ref('未命名文件')
const isSaved = ref(true)
const saveStatus = ref('已儲存')
const showSettings = ref(false)

// 設定相關
const autoSaveInterval = ref(30)
const fontSize = ref('medium')
let autoSaveTimer = null

// 主題切換
const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  // 發出事件通知父組件
  emit('theme-change', theme.value)
}

// 側邊欄控制
const emit = defineEmits(['toggle-sidebar', 'theme-change', 'font-size-change'])
const toggleSidebar = () => {
  emit('toggle-sidebar')
}

// 儲存功能
const saveContent = () => {
  isSaved.value = false
  saveStatus.value = '儲存中...'
  
  // 調用父組件的儲存方法
  const success = handleSave()
  
  if (success) {
    setTimeout(() => {
      isSaved.value = true
      saveStatus.value = '已儲存'
    }, 1000)
  } else {
    saveStatus.value = '儲存失敗'
  }
}

// 自動儲存設定
const updateAutoSaveInterval = () => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
  
  if (autoSaveInterval.value >= 5) {
    autoSaveTimer = setInterval(saveContent, autoSaveInterval.value * 1000)
  }
}

// 字體大小設定
const updateFontSize = () => {
  emit('font-size-change', fontSize.value)
}

// 生命週期鉤子
onMounted(() => {
  updateAutoSaveInterval()
  updateFontSize()
})

onUnmounted(() => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
})
</script>

<style scoped>
.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  height: 60px;
  border-bottom: 1px solid var(--border-color);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.nav-container.light {
  background-color: #ffffff;
  --border-color: #e2e8f0;
  --text-color: #1a1a1a;
  --icon-color: #4a5568;
}

.nav-container.dark {
  background-color: #1a1a1a;
  --border-color: #2d2d2d;
  --text-color: #ffffff;
  --icon-color: #a0aec0;
}

.left-section,
.center-section,
.right-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  color: var(--icon-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

button:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.file-name {
  color: var(--text-color);
  font-weight: 500;
}

.save-btn {
  background-color: #2563eb;
  color: white;
  padding: 0.5rem 1rem;
}

.save-btn:hover {
  background-color: #1d4ed8;
}

.save-btn.saved {
  background-color: #059669;
}

.settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
}

.settings-content {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 1.5rem;
  width: 400px;
  max-width: 90vw;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.settings-header h3 {
  margin: 0;
  color: var(--text-color);
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-item label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.setting-item input,
.setting-item select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.light {
  --bg-color: #ffffff;
}

.dark {
  --bg-color: #1a1a1a;
}

.mdi {
  font-size: 1.2rem;
}
</style>
