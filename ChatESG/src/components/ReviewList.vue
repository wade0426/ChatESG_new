<!-- 審核列表組件 -->
<template>
  <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
  <Header @openNav="openNav" />

  <div class="review-list-container">
    <div class="review-list">
      <div class="review-header">
        <h2>待審核列表</h2>
        <div class="filters">
          <el-select v-model="filterStatus" placeholder="狀態篩選" class="filter-select" style="display: none;">
            <el-option
              v-for="(status, key) in reviewStore.reviewStatus"
              :key="key"
              :label="status.label"
              :value="key"
            />
          </el-select>
          <el-input
            v-model="searchQuery"
            placeholder="搜尋..."
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <el-table
        :data="filteredReviews"
        style="width: 100%"
        :row-class-name="getRowClassName"
        class="custom-table"
        height="calc(100vh - 280px)"
      >
        <el-table-column prop="title" label="標題" min-width="100">
          <template #default="scope">
            <router-link :to="'/review?id=' + scope.row.workflow_instance_id" class="title-link">
              {{ scope.row.title }}
            </router-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="submitter" label="提交者" width="120"/>
        
        <el-table-column prop="submitted_at" label="提交時間" width="200">
          <template #default="scope">
            {{ formatDate(scope.row.submitted_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="handleReview(scope.row)"
              class="review-button"
            >
              審核
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReviewStore } from '@/stores/review'
import { useUserStore } from '@/stores/user'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const router = useRouter()
const reviewStore = useReviewStore()
const userStore = useUserStore()

// 篩選和搜尋
const filterStatus = ref('')
const searchQuery = ref('')
const isSidebarOpen = ref(false)

// 計算過濾後的列表
const filteredReviews = computed(() => {
  let filtered = reviewStore.pendingReviews

  // 狀態篩選
  if (filterStatus.value) {
    filtered = filtered.filter(item => item.status === filterStatus.value)
  }

  // 搜尋過濾
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item =>
      item.title.toLowerCase().includes(query) ||
      item.submitter.toLowerCase().includes(query)
    )
  }

  return filtered
})

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 獲取狀態類型
const getStatusType = (status) => {
  const statusMap = {
    DRAFT: 'info',
    REVIEWING: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger'
  }
  return statusMap[status] || 'info'
}

// 處理審核按鈕點擊
const handleReview = (row) => {
  router.push(`/review?id=${row.workflow_instance_id}`)
}

// 獲取行樣式
const getRowClassName = ({ row }) => {
  if (!row) return ''
  return {
    'review-row': true,
    'review-row--urgent': row.isUrgent
  }
}

const openNav = () => {
    isSidebarOpen.value = true
}

const closeNav = () => {
    isSidebarOpen.value = false
}

// 組件掛載時獲取數據
onMounted(async () => {
  try {
    await reviewStore.fetchPendingReviews(userStore.userID)
  } catch (error) {
    console.error('Error fetching reviews:', error)
    ElMessage.error('獲取待審核列表失敗')
  }
})
</script>

<style scoped>
.review-list-container {
  min-height: calc(100vh - 60px);
  padding: 32px;
  background-color: #121212;
}

.review-list {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
  background-color: #1E1E1E;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.review-header {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 32px;
}

.review-header h2 {
  color: #FFFFFF;
  margin: 0;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.filters {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: flex-end;
}

.filter-select {
  width: 160px;
}

.search-input {
  width: 240px;
}

/* 统一输入框和选择框样式 */
:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper) {
  background-color: #2C2C2C !important;
  border: 1px solid #3A3A3A !important;
  box-shadow: none !important;
  transition: all 0.3s ease;
  padding: 8px 12px;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select .el-input__wrapper:hover) {
  border-color: #4497F7 !important;
  background-color: #333333 !important;
}

:deep(.el-input__inner) {
  color: #FFFFFF !important;
  font-size: 14px;
  letter-spacing: 0.3px;
}

:deep(.el-input__inner::placeholder) {
  color: #909399 !important;
}

/* 下拉菜单的完整样式覆盖 */
:deep(.el-select-dropdown.el-popper),
:deep(.el-select__popper.el-popper),
:deep(.el-popper.is-light) {
  background-color: #2C2C2C !important;
  border: 1px solid #3A3A3A !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

:deep(.el-popper.is-light .el-popper__arrow::before) {
  background-color: #2C2C2C !important;
  border: 1px solid #3A3A3A !important;
}

:deep(.el-scrollbar),
:deep(.el-select-dropdown .el-scrollbar__wrap),
:deep(.el-select-dropdown__wrap) {
  background-color: #2C2C2C !important;
}

:deep(.el-select-dropdown__list) {
  background-color: #2C2C2C !important;
  padding: 0;
}

:deep(.el-select-dropdown__item) {
  color: #FFFFFF !important;
  height: 40px;
  line-height: 40px;
  padding: 0 16px;
}

:deep(.el-select-dropdown__item:not(.is-disabled):hover) {
  background-color: #3A3A3A !important;
}

:deep(.el-select-dropdown__item.selected) {
  background-color: #3A3A3A !important;
  color: #4497F7 !important;
  font-weight: 500;
}

/* 修复选择框的样式 */
:deep(.el-select .el-input .el-input__wrapper) {
  background-color: #2C2C2C !important;
  box-shadow: none !important;
  border: 1px solid #3A3A3A !important;
}

:deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: none !important;
  border-color: #4497F7 !important;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: #4497F7 !important;
}

:deep(.el-select .el-input__inner) {
  color: #FFFFFF !important;
}

:deep(.el-select .el-input .el-select__caret) {
  color: #909399 !important;
}

:deep(.el-select .el-input .el-select__caret:hover) {
  color: #FFFFFF !important;
}

/* 确保滚动条样式也符合深色主题 */
:deep(.el-select-dropdown .el-scrollbar__wrap) {
  scrollbar-width: thin;
  scrollbar-color: #4497F7 #2C2C2C;
}

:deep(.el-select-dropdown .el-scrollbar__wrap::-webkit-scrollbar) {
  width: 6px;
}

:deep(.el-select-dropdown .el-scrollbar__wrap::-webkit-scrollbar-track) {
  background: #2C2C2C;
  border-radius: 3px;
}

:deep(.el-select-dropdown .el-scrollbar__wrap::-webkit-scrollbar-thumb) {
  background: #4497F7;
  border-radius: 3px;
}

:deep(.el-select-dropdown .el-scrollbar__wrap::-webkit-scrollbar-thumb:hover) {
  background: #5DAAFF;
}

:deep(.el-table) {
  background-color: #1E1E1E !important;
  color: #FFFFFF !important;
  border: none !important;
  --el-table-row-hover-bg-color: #2C2C2C;
  height: 100%;
}

:deep(.el-table__header) {
  background-color: #2C2C2C !important;
}

:deep(.el-table__header-wrapper th) {
  background-color: #2C2C2C !important;
  color: #FFFFFF !important;
  border-bottom: 2px solid #3A3A3A !important;
  padding: 16px 8px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

:deep(.el-table__row) {
  background-color: #1E1E1E !important;
  transition: background-color 0.2s ease;
}

:deep(.el-table td) {
  padding: 16px 8px;
  border-bottom: 1px solid #2C2C2C !important;
  font-size: 14px;
  letter-spacing: 0.3px;
  line-height: 1.5;
}

.title-link {
  color: #4497F7;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
}

.title-link:hover {
  color: #5DAAFF;
  text-decoration: none;
  opacity: 0.9;
}

.status-tag {
  border: none;
  padding: 6px 12px;
  font-weight: 500;
  border-radius: 6px;
}

.review-button {
  background-color: #4497F7;
  border: none;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.2s ease;
  border-radius: 6px;
}

.review-button:hover {
  background-color: #5DAAFF;
  transform: translateY(-1px);
}

.review-button:active {
  transform: translateY(0);
}

.review-row--urgent {
  background-color: rgba(245, 108, 108, 0.15) !important;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
  letter-spacing: 0.3px;
}
</style> 