<!-- 審核詳情頁面 -->
<template>
  <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
  <Header @openNav="openNav" />

  <div class="review-detail">
    <!-- 頂部進度條 -->
    <div class="review-progress">
      <el-steps :active="currentStep" finish-status="success">
        <el-step
          v-for="(step, index) in reviewSteps"
          :key="index"
          :title="step.title"
          :description="step.description"
        />
      </el-steps>
    </div>

    <div class="review-content">
      <!-- 左側內容區 -->
      <div class="content-section">
        <div class="content-header">
          <h2>{{ currentReview?.title }}</h2>
          <!-- <el-tag :type="getStatusType(currentReview?.status)">
            {{ reviewStore.reviewStatus[currentReview?.status]?.label }}
          </el-tag> -->
        </div>

        <!-- 章節內容顯示 -->
        <div class="chapters-container">
          <template v-for="(chapter, chapterIndex) in currentReview?.chapters" :key="chapterIndex">
            <div class="chapter">
              <h3>{{ chapter.chapterTitle }}</h3>
              
              <template v-for="(subChapter, subIndex) in chapter.subChapters" :key="subIndex">
                <div class="sub-chapter">
                  <h4>{{ subChapter.subChapterTitle }}</h4>
                  
                  <!-- 文字內容 -->
                  <div class="content-text">
                    {{ subChapter.txt }}
                  </div>
                  
                  <!-- 圖片內容 -->
                  <div v-if="subChapter.img_content?.length" class="content-images">
                    <div v-for="(img, imgIndex) in subChapter.img_content" :key="imgIndex" class="image-container">
                      <el-image
                        :src="img.url"
                        :preview-src-list="[img.url]"
                        :preview-teleported="true"
                        :initial-index="imgIndex"
                        fit="cover"
                        class="content-image"
                        loading="lazy"
                      />
                      <div class="image-info" v-if="img.title || img.subtitle">
                        <h5 v-if="img.title">{{ img.title }}</h5>
                        <p v-if="img.subtitle">{{ img.subtitle }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>

      <!-- 右側審核區 -->
      <div class="review-section">
        <!-- 審核意見輸入 -->
        <div class="review-input">
          <h3>審核意見</h3>
          <el-input
            v-model="reviewComment"
            type="textarea"
            :rows="6"
            placeholder="請輸入審核意見..."
          />
          
          <div class="review-actions">
            <el-button type="success" @click="handleApprove">
              通過審核
            </el-button>
            <el-button type="danger" @click="handleReject">
              退回修改
            </el-button>
          </div>
        </div>

        <!-- 審核歷程 -->
        <div class="review-history">
          <div class="history-header">
            <h3>審核歷程</h3>
            <el-button type="primary" link @click="toggleHistory">
              {{ showHistory ? '收起' : '展開' }}
            </el-button>
          </div>
          
          <div v-show="showHistory" class="history-content">
            <el-timeline>
              <el-timeline-item
                v-for="(history, index) in reviewHistory"
                :key="index"
                :type="getHistoryType(history.status)"
                :timestamp="formatDate(history.time)"
              >
                <h4>{{ history.reviewer }}</h4>
                <p>{{ history.comment }}</p>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useReviewStore } from '@/stores/review'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import { useUserStore } from '@/stores/user'

const isSidebarOpen = ref(false)
const route = useRoute()
const router = useRouter()
const reviewStore = useReviewStore()
const userStore = useUserStore()

const openNav = () => {
    isSidebarOpen.value = true
}

const closeNav = () => {
    isSidebarOpen.value = false
}

// 審核步驟
const reviewSteps = [
  { title: '提交審核', description: '等待審核' },
  { title: '初審', description: '部門主管審核' },
  { title: '複審', description: '高層審核' },
  { title: '完成', description: '審核完成' }
]

const currentStep = ref(1) // 審核步驟
const reviewComment = ref('') // 審核意見
const showHistory = ref(false) // 是否顯示審核歷程
const currentReview = ref(null) // 當前審核內容
const reviewHistory = ref([]) // 審核歷程

// 獲取狀態類型
const getStatusType = (status) => {
  const statusMap = {
    DRAFT: 'info',
    REVIEWING: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger'
  }
  return statusMap[status]
}

// 獲取歷程類型
const getHistoryType = (status) => {
  const typeMap = {
    APPROVED: 'success',
    REJECTED: 'danger',
    REVIEWING: 'warning'
  }
  return typeMap[status] || 'info'
}

// 格式化日期
const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 切換歷程顯示
const toggleHistory = () => {
  showHistory.value = !showHistory.value
}

// 處理審核通過
const handleApprove = async () => {
  if (!reviewComment.value.trim()) {
    ElMessage.warning('請輸入審核意見')
    return
  }

  try {
    await ElMessageBox.confirm('確定通過此審核？', '確認', {
      confirmButtonText: '確定',
      cancelButtonText: '取消',
      type: 'success'
    })

    await reviewStore.submitReview(
      route.query.id,
      userStore.userID,
      'approved',
      reviewComment.value
    )

    ElMessage.success('審核已通過')
    router.push('/review-list')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失敗')
    }
  }
}

// 處理審核退回
const handleReject = async () => {
  if (!reviewComment.value.trim()) {
    ElMessage.warning('請輸入退回原因')
    return
  }

  try {
    await ElMessageBox.confirm('確定退回此審核？', '確認', {
      confirmButtonText: '確定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await reviewStore.submitReview(
      route.query.id,
      userStore.userID,
      'rejected',
      reviewComment.value
    )

    ElMessage.success('已退回修改')
    router.push('/review-list')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失敗')
    }
  }
}

// 初始化數據
onMounted(async () => {
  try {
    // 判斷是否有get id
    if (!route.query.id) {
      router.push('/home')
      return
    }

    console.log("開始獲取審核資料，ID:", route.query.id)
    // 獲取審核資料內容
    await reviewStore.fetchReviewData(route.query.id)
    
    // 直接使用 store 中處理好的數據
    currentReview.value = reviewStore.currentReview
    console.log("組件中的數據:", currentReview.value)
    
    // // 獲取審核歷程
    // await reviewStore.fetchReviewHistory(route.query.id)
    // reviewHistory.value = reviewStore.reviewHistory
  } catch (error) {
    ElMessage.error('獲取數據失敗')
    console.error('獲取數據失敗:', error)
  }
})
</script>

<style scoped>
.review-detail {
  padding: 20px;
  background-color: #1E1E1E;
  min-height: calc(100vh - 60px);
  color: #F0F0F0;
}

.review-progress {
  margin: 0 -20px 24px;
  padding: 32px 40px;
  background-color: #262626;
  border-radius: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

:deep(.el-steps) {
  --el-text-color-regular: #AAAAAA;
  --el-text-color-primary: #F0F0F0;
}

:deep(.el-step__title) {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

:deep(.el-step__description) {
  font-size: 14px;
  color: #999999;
}

:deep(.el-step__head.is-process) {
  color: #5B8FF9;
  border-color: #5B8FF9;
}

:deep(.el-step__head.is-success) {
  color: #67C23A;
  border-color: #67C23A;
}

.review-content {
  display: flex;
  gap: 24px;
  height: calc(100vh - 200px);
}

.content-section {
  flex: 1;
  background-color: #262626;
  border-radius: 12px;
  padding: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #333333;
}

.content-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #FFFFFF;
}

.chapters-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 16px;
}

.chapters-container::-webkit-scrollbar {
  width: 6px;
}

.chapters-container::-webkit-scrollbar-thumb {
  background-color: #444444;
  border-radius: 3px;
}

.chapter {
  margin-bottom: 32px;
}

.chapter h3 {
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.sub-chapter {
  margin: 20px 0;
  padding-left: 20px;
  border-left: 2px solid #333333;
}

.sub-chapter h4 {
  color: #F0F0F0;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.6;
  margin: 12px 0;
  color: #D0D0D0;
}

.content-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin: 16px 0;
  will-change: transform;
  transform: translateZ(0);
}

.image-container {
  position: relative;
  width: 100%;
  height: 150px;
  border-radius: 8px;
  transition: transform 0.2s;
  will-change: transform;
  transform: translateZ(0);
  overflow: hidden;
}

.image-container:hover {
  transform: scale(1.02);
}

.content-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
  transition: transform 0.2s;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.image-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 0 0 8px 8px;
}

.image-info h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #FFFFFF;
}

.image-info p {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #FFFFFF;
}

.review-section {
  width: 380px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.review-input,
.review-history {
  background-color: #262626;
  border-radius: 12px;
  padding: 24px;
}

.review-input h3,
.review-history h3 {
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

:deep(.el-textarea__inner) {
  background-color: #333333;
  border: 1px solid #444444;
  color: #F0F0F0;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.3s;
}

:deep(.el-textarea__inner:focus) {
  border-color: #5B8FF9;
  box-shadow: 0 0 0 2px rgba(91, 143, 249, 0.2);
}

:deep(.el-textarea__inner::placeholder) {
  color: #666666;
}

.review-actions {
  margin-top: 20px;
  display: flex;
  gap: 16px;
  justify-content: flex-end;
}

:deep(.el-button) {
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 500;
  transition: all 0.3s;
}

:deep(.el-button--success) {
  background-color: #2B7254;
  border-color: #2B7254;
}

:deep(.el-button--success:hover) {
  background-color: #338662;
  border-color: #338662;
}

:deep(.el-button--danger) {
  background-color: #8B3E3E;
  border-color: #8B3E3E;
}

:deep(.el-button--danger:hover) {
  background-color: #A04747;
  border-color: #A04747;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.history-content {
  max-height: calc(100vh - 500px);
  overflow-y: auto;
  padding-right: 16px;
}

:deep(.el-timeline-item__node) {
  background-color: #333333;
  border-color: #444444;
}

:deep(.el-timeline-item__content) {
  color: #D0D0D0;
}

:deep(.el-timeline-item__timestamp) {
  color: #999999;
}

:deep(.el-tag) {
  background-color: transparent;
  border-width: 1px;
  font-weight: 500;
  padding: 4px 12px;
}

:deep(.el-image-viewer__wrapper) {
  position: fixed;
  z-index: 2000;
}

:deep(.el-image-viewer__mask) {
  position: fixed;
  z-index: 2000;
}

:deep(.el-image-viewer__btn) {
  z-index: 2001;
}

:deep(.el-image-viewer__canvas) {
  z-index: 2001;
  will-change: transform;
  transform: translateZ(0);
}

:deep(.el-image-viewer__actions) {
  z-index: 2001;
}
</style> 