<template>
  <div class="major-issues-container">

    <!-- 引入頂部導航欄 -->
    <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
    <Header @openNav="openNav" />

    <h1 class="page-title">請選擇您想要遵守的重大主題</h1>
    
    <!-- 文件名稱和搜尋區域 -->
    <div class="file-search-container">
      <div class="file-name-section">
        <input
          v-model="fileName"
          type="text"
          class="file-name-input"
          placeholder="文件名稱"
          @input="handleContentChange"
        />
        <button 
          @click="saveFile" 
          class="save-button"
          :class="{
            'saving': saveStatus === 'saving',
            'saved': saveStatus === 'saved',
            'error': saveStatus === 'error',
            'unsaved': saveStatus === 'unsaved'
          }"
          :disabled="saveStatus === 'saving' || saveStatus === 'saved'"
        >
          <span class="save-icon" v-if="saveStatus === 'saving'">
            <i class="fas fa-spinner fa-spin"></i>
          </span>
          <span class="save-icon" v-else-if="saveStatus === 'saved'">
            <i class="fas fa-check"></i>
          </span>
          <span class="save-icon" v-else-if="saveStatus === 'error'">
            <i class="fas fa-exclamation-circle"></i>
          </span>
          <span class="save-icon" v-else-if="saveStatus === 'unsaved'">
            <i class="fas fa-save"></i>
          </span>
          {{ getSaveButtonText }}
        </button>
      </div>
      <div class="search-section">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜尋議題、領域或說明..."
          class="search-input"
        />
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <table class="issues-table">
        <thead>
          <tr>
            <th class="checkbox-column">
              <input
                type="checkbox"
                v-model="selectAll"
                @change="toggleSelectAll"
              />
            </th>
            <th @click="sort('theme')" :class="{ active: sortKey === 'theme' }">
              議題
              <span class="sort-icon">{{ getSortIcon('theme') }}</span>
            </th>
            <th @click="sort('domain')" :class="{ active: sortKey === 'domain' }">
              領域
              <span class="sort-icon">{{ getSortIcon('domain') }}</span>
            </th>
            <th @click="sort('description')" :class="{ active: sortKey === 'description' }">
              說明
              <span class="sort-icon">{{ getSortIcon('description') }}</span>
            </th>
            <th @click="sort('gri_id')" :class="{ active: sortKey === 'gri_id' }">
              GRI_ID
              <span class="sort-icon">{{ getSortIcon('gri_id') }}</span>
            </th>
            <th @click="sort('gri_name')" :class="{ active: sortKey === 'gri_name' }">
              GRI_NAME
              <span class="sort-icon">{{ getSortIcon('gri_name') }}</span>
            </th>
            <th @click="sort('sasb')" :class="{ active: sortKey === 'sasb' }">
              SASB
              <span class="sort-icon">{{ getSortIcon('sasb') }}</span>
            </th>
            <th @click="sort('sdgs')" :class="{ active: sortKey === 'sdgs' }">
              SDGs
              <span class="sort-icon">{{ getSortIcon('sdgs') }}</span>
            </th>
            <th @click="sort('tcfd')" :class="{ active: sortKey === 'tcfd' }">
              TCFD
              <span class="sort-icon">{{ getSortIcon('tcfd') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredAndSortedIssues" :key="item.id">
            <td class="checkbox-column">
              <input
                type="checkbox"
                v-model="selectedIssues"
                :value="item.id"
              />
            </td>
            <td>{{ item.theme }}</td>
            <td>{{ item.domain }}</td>
            <td>{{ item.description }}</td>
            <td>{{ item.gri_id }}</td>
            <td>{{ item.gri_name }}</td>
            <td>{{ item.sasb }}</td>
            <td>{{ Array.isArray(item.sdgs) ? item.sdgs.join(', ') : item.sdgs }}</td>
            <td>{{ item.tcfd }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import axios from 'axios'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import { useUserStore } from '@/stores/user'
import { useCriteriaTemplateStore } from '@/stores/criteriaTemplate'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
// import { toast } from 'vue-toastification'

// 用戶狀態管理
const userStore = useUserStore()
const criteriaTemplateStore = useCriteriaTemplateStore()
const router = useRouter()
const route = useRoute()

const initializeUser = async () => {
  if (!userStore.isAuthenticated) {
    userStore.initializeFromStorage()
    if (!userStore.isAuthenticated) {
      router.push('/login')
      return
    }
  }
  await userStore.fetchUserProfile()
}

const initializeCriteriaTemplate = async () => {
  const assetId = route.query.assetId
  if (!assetId) {
    router.push('/home')
    return
  }
  criteriaTemplateStore.setAssetID(assetId)
  criteriaTemplateStore.setOrganizationID(userStore.organizationID)
  criteriaTemplateStore.setRoleIDs(userStore.organizationRoles.map(role => role.roleID).join(','))
  criteriaTemplateStore.setUserID(userStore.userID)
  criteriaTemplateStore.fetchCriteriaTemplate()
}

// 在組件掛載時初始化
onMounted(async () => {
  await initializeUser()
  await fetchData() // 先获取数据
  await initializeCriteriaTemplate() // 然后初始化模板
  
  window.addEventListener('beforeunload', handleBeforeUnload)
})

// 監聽路由變化
watch(
  () => route.fullPath,
  async () => {
    await initializeUser()
  }
)

// 導覽列狀態
const isSidebarOpen = ref(false)

// 導覽列方法
const openNav = () => {
  isSidebarOpen.value = true
}

const closeNav = () => {
  isSidebarOpen.value = false
}

// 數據狀態
const issues = ref([])
const selectedIssues = ref([])
const searchQuery = ref('')
const sortKey = ref('gri_id')
const sortOrder = ref('asc')
const selectAll = ref(false)

// 文件名稱狀態
const fileName = computed({
  get: () => criteriaTemplateStore.fileName,
  set: (value) => criteriaTemplateStore.setFileName(value)
})

// 儲存狀態管理
const saveStatus = ref('saved') // 'saved', 'saving', 'unsaved', 'error'
const lastSavedData = ref(null)
const autoSaveTimeout = ref(null)

// 計算儲存按鈕文字
const getSaveButtonText = computed(() => {
  switch (saveStatus.value) {
    case 'saving':
      return '儲存中...'
    case 'saved':
      return '已儲存'
    case 'error':
      return '儲存失敗'
    case 'unsaved':
      return '儲存'
    default:
      return '儲存'
  }
})

// 監聽內容變化
const handleContentChange = () => {
  saveStatus.value = 'unsaved'
  
  // 清除之前的自動儲存計時器
  if (autoSaveTimeout.value) {
    clearTimeout(autoSaveTimeout.value)
  }
  
  // 設置新的自動儲存計時器（10秒後自動儲存）
  autoSaveTimeout.value = setTimeout(() => {
    if (saveStatus.value === 'unsaved') {
      saveFile()
    }
  }, 10000)
}

// 修改 fetchData 函数
const fetchData = async () => {
  try {
    const response = await axios.get('https://raw.githubusercontent.com/wade0426/1110932038/refs/heads/main/Major_Issues_List.csv')
    const csvData = response.data.trim()
    
    // 解析 CSV 數據
    const rows = csvData.split('\n')
    const headers = rows[0].split(',') // 保存標題行以供參考
    
    // 從第二行開始處理數據
    const processedIssues = rows.slice(1)
      .map((row, index) => {
        // 使用更精確的 CSV 解析邏輯
        let columns = []
        let inQuotes = false
        let currentValue = ''
        
        for (let i = 0; i < row.length; i++) {
          const char = row[i]
          
          if (char === '"') {
            inQuotes = !inQuotes
          } else if (char === ',' && !inQuotes) {
            columns.push(currentValue.trim())
            currentValue = ''
          } else {
            currentValue += char
          }
        }
        columns.push(currentValue.trim()) // 添加最後一列
        
        // 清理數據：移除引號和多餘的空格
        columns = columns.map(col => col.replace(/^"|"$/g, '').trim())
        
        // 處理 SDGs：如果包含分號，則分割為數組
        const sdgsValue = columns[6] || ''
        const sdgs = sdgsValue.includes(';') 
          ? sdgsValue.split(';').map(s => s.trim())
          : sdgsValue.split(',').map(s => s.trim()).filter(s => s)
        
        return {
          id: index,
          theme: columns[0],
          domain: columns[1],
          description: columns[2],
          gri_id: columns[3],
          gri_name: columns[4],
          sasb: columns[5] || null,
          sdgs: sdgs.length > 0 ? sdgs : null,
          tcfd: columns[7] || null
        }
      })
      .filter(item => item.theme && !headers.includes(item.theme)) // 過濾掉標題行和空行
    
    // 一次性更新 issues
    issues.value = processedIssues
    
  } catch (error) {
    console.error('Error fetching data:', error)
  }
}

// 過濾和排序
const filteredAndSortedIssues = computed(() => {
  let result = [...issues.value]
  
  // 搜索過濾
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(item => 
      (item.theme?.toLowerCase().includes(query) || false) ||
      (item.domain?.toLowerCase().includes(query) || false) ||
      (item.description?.toLowerCase().includes(query) || false) ||
      (item.gri_id?.toString().includes(query) || false) ||
      (item.gri_name?.toLowerCase().includes(query) || false) ||
      (item.sasb?.toLowerCase().includes(query) || false) ||
      (item.sdgs?.toLowerCase().includes(query) || false) ||
      (item.tcfd?.toLowerCase().includes(query) || false)
    )
  }
  
  // 排序
  result.sort((a, b) => {
    const aValue = a[sortKey.value] || ''
    const bValue = b[sortKey.value] || ''
    
    // 對於數字類型的列使用數字排序
    if (sortKey.value === 'gri_id') {
      const aNum = parseInt(aValue) || 0
      const bNum = parseInt(bValue) || 0
      return sortOrder.value === 'asc' 
        ? aNum - bNum
        : bNum - aNum
    }
    
    // 其他列使用字符串排序
    if (sortOrder.value === 'asc') {
      return aValue.localeCompare(bValue, 'zh-TW')
    } else {
      return bValue.localeCompare(aValue, 'zh-TW')
    }
  })
  
  return result
})

// 排序方法
const sort = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

// 獲取排序圖標
const getSortIcon = (key) => {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

// 修改 selectedIssues 的监听器，添加防递归标记
let isUpdatingFromStore = false
let isUpdatingFromSelection = false

// 修改 criteriaTemplateStore 监听器
watch(() => criteriaTemplateStore.selectedCriteria, (newCriteria) => {
  if (isUpdatingFromSelection || !issues.value.length) return
  
  isUpdatingFromStore = true
  try {
    // 根據 gri_id 找到對應的 issues 並設置選中狀態
    const newSelectedIssues = issues.value
      .filter(item => newCriteria.some(sc => sc.gri_id === item.gri_id))
      .map(item => item.id)
    
    // 只有当选中状态真的改变时才更新
    if (JSON.stringify(newSelectedIssues) !== JSON.stringify(selectedIssues.value)) {
      selectedIssues.value = newSelectedIssues
      // 更新全選狀態
      selectAll.value = selectedIssues.value.length === issues.value.length
    }
  } finally {
    isUpdatingFromStore = false
  }
}, { immediate: true })

// 修改 selectedIssues 监听器
watch(selectedIssues, (newVal, oldVal) => {
  if (isUpdatingFromStore || !issues.value.length) return
  
  // 只有当选中状态真的改变时才更新
  if (JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
    isUpdatingFromSelection = true
    try {
      const selectedItems = issues.value
        .filter(item => newVal.includes(item.id))
        .map(item => ({
          gri_id: item.gri_id,
          topic: item.theme,
          domain: item.domain,
          description: item.description,
          gri_name: item.gri_name,
          sdgs: Array.isArray(item.sdgs) ? item.sdgs : (item.sdgs ? item.sdgs.split(',').map(s => s.trim()) : null),
          tcfd: item.tcfd || null,
          sasb: item.sasb || null
        }))
      criteriaTemplateStore.setSelectedCriteria(selectedItems)
      handleContentChange()
    } finally {
      isUpdatingFromSelection = false
    }
  }
}, { deep: true })

// 修改 toggleSelectAll 函数
const toggleSelectAll = () => {
  isUpdatingFromSelection = true
  try {
    if (selectAll.value) {
      const selectedItems = filteredAndSortedIssues.value.map(item => ({
        gri_id: item.gri_id,
        topic: item.theme,
        domain: item.domain,
        description: item.description,
        gri_name: item.gri_name,
        sdgs: Array.isArray(item.sdgs) ? item.sdgs : (item.sdgs ? item.sdgs.split(',').map(s => s.trim()) : null),
        tcfd: item.tcfd || null,
        sasb: item.sasb || null
      }))
      criteriaTemplateStore.setSelectedCriteria(selectedItems)
      selectedIssues.value = filteredAndSortedIssues.value.map(item => item.id)
    } else {
      criteriaTemplateStore.clearSelectedCriteria()
      selectedIssues.value = []
    }
  } finally {
    isUpdatingFromSelection = false
  }
}

// 修改 handleBeforeUnload 函数
const handleBeforeUnload = (event) => {
  if (saveStatus.value === 'unsaved') {
    const message = '您有未儲存的更改，確定要離開嗎？'
    event.preventDefault()
    event.returnValue = message
    return message
  }
}

// 添加路由离开守卫
onBeforeRouteLeave((to, from, next) => {
  if (saveStatus.value === 'unsaved') {
    const answer = window.confirm('您有未儲存的更改，確定要離開嗎？')
    if (answer) {
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})

// 修改 saveFile 函数，确保保存成功后正确更新状态
const saveFile = async () => {
  try {
    saveStatus.value = 'saving'
    
    await criteriaTemplateStore.saveCriteriaTemplate()
    
    saveStatus.value = 'saved'
    lastSavedData.value = JSON.stringify({
      selectedCriteria: criteriaTemplateStore.selectedCriteria,
      fileName: criteriaTemplateStore.fileName
    })
    
    // 3秒後隱藏成功狀態
    setTimeout(() => {
      if (saveStatus.value === 'saved') {
        saveStatus.value = 'saved'
      }
    }, 3000)
    
  } catch (error) {
    console.error('儲存失敗:', error)
    saveStatus.value = 'error'
  }
}

// 监听数据变化，更新保存状态
watch([
  () => criteriaTemplateStore.selectedCriteria,
  () => criteriaTemplateStore.fileName
], () => {
  const currentData = JSON.stringify({
    selectedCriteria: criteriaTemplateStore.selectedCriteria,
    fileName: criteriaTemplateStore.fileName
  })
  
  if (lastSavedData.value !== currentData) {
    saveStatus.value = 'unsaved'
  }
}, { deep: true })
</script>

<style scoped>
.major-issues-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #1a1a1a;
  color: white;
  min-height: 100vh;
  padding-top: 80px; /* 為頂部導覽列預留空間 */
}

/* 添加頂部導覽列相關樣式 */
:deep(.header) {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background-color: #1c1c1e;
  border-bottom: 1px solid #2c2c2e;
}

:deep(.sidebar) {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 1000;
  background-color: #1c1c1e;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: white;
  margin-bottom: 2rem;
  margin-top: 2rem;
  text-align: center;
}

.file-search-container {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: center;
}

.file-name-section {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex: 1;
}

.file-name-input {
  flex: 1;
  padding: 0.8rem 1rem;
  font-size: 1rem;
  border: 1px solid #333;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s ease;
  background-color: #2a2a2a;
  color: white;
  max-width: 300px;
}

.file-name-input:focus {
    border-color: #0084ff;
    box-shadow: 0 0 0 3px rgba(0, 132, 255, 0.1);
}

.save-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.5rem;
  font-size: 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-button.saving {
  background-color: #666;
  cursor: not-allowed;
}

.save-button.saved {
  background-color: #28a745;
  cursor: default;
  color: white;
}

.save-button.error {
  background-color: #dc3545;
}

.save-button.unsaved {
  background-color: #0084ff;
  animation: pulse 2s infinite;
}

.save-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

.search-section {
  flex: 2;
}

.search-input {
  width: 100%;
  /* max-width: 400px; */
  padding: 0.8rem 1rem;
  font-size: 1rem;
  border: 1px solid #333;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s ease;
  background-color: #2a2a2a;
  color: white;
}

.search-input:focus {
  border-color: #0084ff;
  box-shadow: 0 0 0 3px rgba(0, 132, 255, 0.1);
}

.search-input::placeholder {
  color: #666;
}

.table-container {
  width: 100%;
  overflow-x: auto;
  background: #2a2a2a;
  border-radius: 10px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
  -webkit-overflow-scrolling: touch; /* 為 iOS 設備提供更流暢的滾動 */
}

.issues-table {
  width: 100%;
  min-width: 800px; /* 確保表格在小螢幕上有最小寬度 */
  border-collapse: collapse;
  text-align: left;
}

.issues-table th {
  background-color: #333;
  padding: 1rem;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  border-bottom: 1px solid #444;
}

.issues-table th:hover {
  background-color: #404040;
}

.issues-table td {
  padding: 1rem;
  border-top: 1px solid #333;
  color: #fff;
}

.issues-table tr:hover {
  background-color: #333;
}

.checkbox-column {
  width: 40px;
  text-align: center;
}

.sort-icon {
  display: inline-block;
  margin-left: 0.5rem;
  color: #666;
}

th.active {
  color: #0084ff;
}

th.active .sort-icon {
  color: #0084ff;
}

input[type="checkbox"] {
  width: 1.2rem;
  height: 1.2rem;
  cursor: pointer;
  background-color: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
}

input[type="checkbox"]:checked {
  background-color: #0084ff;
  border-color: #0084ff;
}

input[type="checkbox"]:hover {
  border-color: #0084ff;
}

/* 添加響應式媒體查詢 */
@media screen and (max-width: 768px) {
  .major-issues-container {
    padding: 0.5rem;
  }

  .page-title {
    font-size: 1.5rem;
    margin-bottom: 1rem;
  }

  .file-search-container {
    flex-direction: column;
    gap: 0.5rem;
  }

  .file-name-section,
  .search-section {
    width: 100%;
  }

  .file-name-input,
  .search-input {
    max-width: none;
  }

  .issues-table th,
  .issues-table td {
    padding: 0.8rem 0.5rem;
    font-size: 0.9rem;
  }
}

@media screen and (max-width: 480px) {
  .page-title {
    font-size: 1.2rem;
  }

  .issues-table th,
  .issues-table td {
    padding: 0.6rem 0.4rem;
    font-size: 0.8rem;
  }
}
</style>