<template>
  <nav :class="['nav-container', theme]">
    <div class="left-section">
      <button class="menu-btn" @click="toggleSidebar">
        <i class="mdi mdi-menu"></i>
      </button>
      <button class="home-btn" @click="goHome">
        <i class="mdi mdi-home"></i>
      </button>
      <div class="file-info">
        <!-- 檔案名稱輸入框 -->
        <input
          type="text"
          :value="fileName"
          class="file-name-input"
          @input="handleFileNameInput"
          @change="handleFileNameChange"
          placeholder="輸入檔案名稱"
          disabled
        >
      </div>
    </div>

    <div class="right-section">
      <!-- 註解篩選按鈕 -->
      <div class="comment-filter">
        <button @click="toggleCommentFilter" class="comment-filter-btn">
          <i class="mdi mdi-message-outline"></i>
          <span class="comment-count" v-if="commentCount > 0">{{ commentCount }}</span>
        </button>
        <div v-if="showFilter" class="comment-filter-dropdown">
          <div class="filter-header">篩選條件</div>
          <div class="filter-options">
            <label class="filter-option">
              <input 
                type="radio" 
                v-model="commentFilter" 
                value="all"
                :checked="commentFilter === 'all'"
                name="commentFilter"
              >
              <span>全部</span>
            </label>
            <label class="filter-option">
              <input 
                type="radio" 
                v-model="commentFilter" 
                value="unfinished"
                :checked="commentFilter === 'unfinished'"
                name="commentFilter"
              >
              <span>未完成</span>
            </label>
            <label class="filter-option">
              <input 
                type="radio" 
                v-model="commentFilter" 
                value="resolved"
                :checked="commentFilter === 'resolved'"
                name="commentFilter"
              >
              <span>已解決</span>
            </label>
          </div>
        </div>
      </div>

      <div class="theme-toggle">
        <button @click="toggleTheme" class="theme-btn">
          <i :class="['mdi', theme === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny']"></i>
        </button>
      </div>

      <!-- 設定按鈕 -->
      <button class="settings-btn" @click="showSettings = true">
        <i class="mdi mdi-cog"></i>
      </button>

      <!-- 儲存按鈕 -->
      <button class="save-btn" @click="saveContent" :class="{ 'saved': isSaved }" style="display: none;">
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

    <!-- 註解聊天窗 -->
    <div v-if="showCommentFilter" class="comment-chat-window">
      <div class="chat-header">
        <div class="header-left">
          <button class="filter-btn" @click="toggleFilter">
            <span>{{ getFilterText() }}</span>
            <i class="mdi mdi-chevron-down"></i>
          </button>
        </div>
        <div class="header-right">
          <button class="header-btn" @click="toggleCommentFilter">
            <i class="mdi mdi-close"></i>
          </button>
        </div>
      </div>
      <div class="chat-content">
        <div v-for="comment in filteredComments" :key="comment.id" class="comment-item">
          <div class="comment-avatar">
            {{ comment.create_user_name?.charAt(0) || 'U' }}
          </div>
          <div class="comment-main">
            <div class="comment-header">
              <span class="comment-author">{{ comment.create_user_name || '使用者' }}</span>
              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>
            <div class="comment-text">{{ comment.content }}</div>
            <div class="comment-section">{{ comment.section }}</div>
            <div class="comment-status" :class="comment.status">
              {{ comment.status === 'resolved' ? '已解決' : '未完成' }}
            </div>
          </div>
          <div class="comment-actions">
            <button 
              class="status-toggle"
              :class="{ 'resolved': comment.status === 'resolved' }"
              @click="toggleCommentStatus(comment)"
            >
              <i class="mdi" :class="comment.status === 'resolved' ? 'mdi-check-circle' : 'mdi-checkbox-blank-circle-outline'"></i>
            </button>
            <div class="more-actions-wrapper">
              <button class="more-actions" @click="toggleMoreActions(comment)">
                <i class="mdi mdi-dots-vertical"></i>
              </button>
              <div v-if="comment.showMoreActions" class="more-actions-dropdown">
                <button class="delete-btn" @click="deleteComment(comment)">
                  <i class="mdi mdi-delete-outline"></i>
                  <span>刪除註解</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted, inject, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCompanyInfoStore } from '@/stores/companyInfo'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const companyInfoStore = useCompanyInfoStore()
const userStore = useUserStore()
// 注入父組件提供的儲存方法
const handleSave = inject('handleSave')

// 注入父組件提供的註解數據
const comments = inject('comments', ref({}))

// 基本狀態
const theme = ref('dark')
const fileNameInput = ref('')  // 新增用於處理輸入的ref
const fileName = computed(() => {
  return companyInfoStore.assetName || '未命名文件'
})
const isSaved = ref(true)
const saveStatus = ref('已儲存')
const showSettings = ref(false)

// 設定相關
const autoSaveInterval = ref(60)
const fontSize = ref('medium')
let autoSaveTimer = null

const showCommentFilter = ref(false)
const commentFilter = ref('all')

// 新增篩選相關的狀態
const showFilter = ref(false)

// 計算註解數量
const commentCount = computed(() => {
  return Object.values(comments.value).filter(comment => 
    comment.status === 'unfinished'
  ).length
})

// 計算過濾後的註解列表
const filteredComments = computed(() => {
  const allComments = Object.entries(comments.value).map(([id, comment]) => ({
    id,
    ...comment
  }))

  switch (commentFilter.value) {
    case 'unfinished':
      return allComments.filter(comment => comment.status === 'unfinished')
    case 'resolved':
      return allComments.filter(comment => comment.status === 'resolved')
    default:
      return allComments
  }
})

// 格式化時間
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffInMinutes = Math.floor((now - date) / 1000 / 60)
  
  if (diffInMinutes < 1) return '剛剛'
  if (diffInMinutes < 60) return `${diffInMinutes} 分鐘前`
  
  const diffInHours = Math.floor(diffInMinutes / 60)
  if (diffInHours < 24) return `${diffInHours} 小時前`
  
  const diffInDays = Math.floor(diffInHours / 24)
  if (diffInDays < 7) return `${diffInDays} 天前`
  
  return date.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 切換註解狀態
const toggleCommentStatus = (comment) => {
  const newStatus = comment.status === 'resolved' ? 'unfinished' : 'resolved'
  comments.value[comment.id] = {
    ...comments.value[comment.id],
    status: newStatus
  }
}

// 主題切換
const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  // 發出事件通知父組件
  emit('theme-change', theme.value)
}

// 側邊欄控制
const emit = defineEmits(['toggle-sidebar', 'theme-change', 'font-size-change', 'comment-filter-change'])
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
  document.addEventListener('click', (event) => {
    const filterEl = document.querySelector('.comment-filter-dropdown')
    const filterBtnEl = document.querySelector('.filter-btn')
    
    // 如果點擊的不是篩選按鈕且不是篩選下拉選單，則關閉篩選選單
    if (filterEl && filterBtnEl && 
        !filterEl.contains(event.target) && 
        !filterBtnEl.contains(event.target)) {
      showFilter.value = false
    }

    // 處理更多選項選單的關閉
    const clickedMoreActionsBtn = event.target.closest('.more-actions')
    const clickedDropdown = event.target.closest('.more-actions-dropdown')
    
    // 如果點擊的不是更多選項按鈕也不是下拉選單內容，則關閉所有下拉選單
    if (!clickedMoreActionsBtn && !clickedDropdown) {
      Object.values(comments.value).forEach(comment => {
        comment.showMoreActions = false
      })
    }
  })
})

onUnmounted(() => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
})

// 回到首頁前先存檔
const goHome = async () => {
  // 先執行存檔
  saveContent()
  // 等待一小段時間確保存檔完成
  setTimeout(() => {
    router.push('/home')
  }, 800)
}

// 監聽 assetContent 變化，更新輸入值
watch(() => companyInfoStore.assetContent?.assetName, (newName) => {
  if (newName) {
    fileNameInput.value = newName
  }
}, { immediate: true })

// 處理輸入
const handleFileNameInput = (event) => {
  fileNameInput.value = event.target.value
}

// 處理確認修改
const handleFileNameChange = async (event) => {
  const newFileName = fileNameInput.value
  try {
    // 檢查必要參數
    if (!route.query.assetId || !userStore.organizationID || !newFileName) {
      throw new Error('缺少必要參數')
    }

    // 檢查名稱長度
    if (newFileName.length > 100) {
      throw new Error('資產名稱長度不能超過100個字符')
    }

    // 調用 API 來更新資產名稱
    const response = await fetch('http://localhost:8000/api/organizations/update_asset_name', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        asset_id: route.query.assetId,
        organization_id: userStore.organizationID,
        asset_name: newFileName
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '更新資產名稱失敗')
    }

    // 更新 store 中的資產名稱
    if (companyInfoStore.assetContent) {
      companyInfoStore.assetContent.assetName = newFileName
    }

    console.log('資產名稱更新成功')
  } catch (error) {
    console.error('更新資產名稱失敗:', error)
    // 發生錯誤時恢復原始名稱
    fileNameInput.value = companyInfoStore.assetContent?.assetName || '未命名文件'
  }
}

// 切換註解篩選下拉選單
const toggleCommentFilter = () => {
  showCommentFilter.value = !showCommentFilter.value
}

// 當篩選條件改變時觸發事件
watch(commentFilter, (newValue) => {
  emit('comment-filter-change', newValue)
})

// 切換篩選下拉選單
const toggleFilter = () => {
  showFilter.value = !showFilter.value
}

// 獲取當前篩選文字
const getFilterText = () => {
  switch (commentFilter.value) {
    case 'all':
      return '全部'
    case 'unfinished':
      return '未完成'
    case 'resolved':
      return '已解決'
    default:
      return '全部'
  }
}

// 當選擇篩選選項時關閉下拉選單
watch(commentFilter, () => {
  showFilter.value = false
})

// 切換更多選項選單
const toggleMoreActions = (comment) => {
  // 確保所有註解都有 showMoreActions 屬性
  Object.values(comments.value).forEach(c => {
    if (c.showMoreActions === undefined) {
      c.showMoreActions = false
    }
  })
  
  // 創建新的註解對象
  const updatedComments = {}
  Object.entries(comments.value).forEach(([id, c]) => {
    updatedComments[id] = {
      ...c,
      showMoreActions: id === comment.id ? !c.showMoreActions : false
    }
  })
  
  // 更新整個 comments 對象
  comments.value = updatedComments
}

// 刪除註解
const deleteComment = (comment) => {
  if (confirm('確定要刪除這個註解嗎？')) {
    delete comments.value[comment.id]
  }
}
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

.home-btn {
  color: var(--icon-color);
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.home-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
  color: #2563eb;
}

.dark .home-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #60a5fa;
}

.file-name-input {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 6px 10px;
  color: var(--text-color);
  font-size: 14px;
  font-weight: 500;
  width: 200px;
  transition: all 0.2s ease;
}

.file-name-input:hover {
  background: rgba(0, 0, 0, 0.05);
}

.dark .file-name-input:hover {
  background: rgba(255, 255, 255, 0.1);
}

.file-name-input:focus {
  outline: none;
  background: var(--bg-color);
  box-shadow: 0 0 0 2px #0066cc;
}

.dark .file-name-input:focus {
  background: rgba(255, 255, 255, 0.05);
}

.file-name-input::placeholder {
  color: var(--text-color);
  opacity: 0.5;
}

.comment-filter {
  position: relative;
  margin-right: 1rem;
}

.comment-filter-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.comment-filter-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .comment-filter-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.comment-filter-btn i {
  font-size: 1.4rem;
}

.comment-count {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background-color: #6264A7;
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.comment-filter-dropdown {
  position: absolute;
  top: 0;
  right: 100%;
  margin-right: 0.5rem;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  min-width: 200px;
  z-index: 1001;
}

.dark .comment-filter-dropdown {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.filter-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  font-weight: 500;
}

.filter-options {
  padding: 0.5rem 0;
}

.filter-option {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.filter-option:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .filter-option:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.filter-option input[type="radio"] {
  margin-right: 0.5rem;
  cursor: pointer;
}

.filter-option span {
  cursor: pointer;
}

.comment-chat-window {
  position: fixed;
  top: 60px;
  right: 0;
  width: 380px;
  height: calc(100vh - 60px);
  background-color: var(--bg-color);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-color);
}

.divider {
  color: var(--border-color);
}

.header-right {
  display: flex;
  gap: 0.5rem;
}

.header-btn {
  padding: 0.5rem;
  border-radius: 4px;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.header-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .header-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.comment-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #6264A7;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.comment-main {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.comment-author {
  font-weight: 600;
  color: var(--text-color);
}

.comment-time {
  color: var(--text-color);
  opacity: 0.6;
  font-size: 0.875rem;
}

.comment-text {
  color: var(--text-color);
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.comment-section {
  font-size: 0.875rem;
  color: var(--text-color);
  opacity: 0.8;
  margin-bottom: 0.5rem;
}

.comment-status {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.comment-status.unfinished {
  background-color: rgba(234, 179, 8, 0.1);
  color: #EAB308;
}

.comment-status.resolved {
  background-color: rgba(5, 150, 105, 0.1);
  color: #059669;
}

.comment-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-toggle {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  border-radius: 4px;
  color: var(--text-color);
  opacity: 0.6;
  transition: all 0.2s ease;
}

.status-toggle:hover {
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.05);
}

.status-toggle.resolved {
  color: #059669;
  opacity: 1;
}

.dark .status-toggle:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.more-actions {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  border-radius: 4px;
  color: var(--text-color);
  opacity: 0.6;
  transition: all 0.2s ease;
}

.more-actions:hover {
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .more-actions:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .filter-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.more-actions-wrapper {
  position: relative;
}

.more-actions-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  min-width: 160px;
  z-index: 1002;
}

.dark .more-actions-dropdown {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.delete-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem 1rem;
  color: #EF4444;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

.dark .delete-btn:hover {
  background-color: rgba(239, 68, 68, 0.2);
}

.delete-btn i {
  font-size: 1.2rem;
}
</style>
