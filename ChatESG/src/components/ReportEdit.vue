<!-- **公司基本資料編輯頁面 (CompanyInfoEdit.vue)** -->

<template>
  <div :class="['editor-container', theme]">
    <!-- 添加 loading 提示訊息 -->
    <div v-if="reportEditStore.loading.isGenerating" class="loading-message">
      <i class="mdi mdi-loading mdi-spin"></i>
      <span>{{ getLoadingMessage }}</span>
    </div>
    <!-- 引入頂部導航欄 -->
    <ReportEditNav 
      @toggle-sidebar="toggleSidebar" 
      @theme-change="handleThemeChange"
      @font-size-change="handleFontSizeChange" 
    />
    
    <!-- 側邊欄 -->
    <div class="sidebar-wrapper">
      <div :class="['sidebar', { 'collapsed': isSidebarCollapsed }]">
        <div class="sidebar-header">
          <h3>報告書編輯</h3>
          <button @click="toggleSidebar" class="sidebar-toggle">
            <i :class="['mdi', isSidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left']"></i>
          </button>
        </div>
        <div class="sidebar-content">
          <div class="add-main-section" style="display: none;">
            <button @click="showAddMainSectionModal" class="add-main-section-btn">
              <i class="mdi mdi-plus"></i>
              <span>新增大章節</span>
            </button>
          </div>
          <!-- 使用 draggable 包裹大章節列表 -->
          <draggable 
            v-model="reportEditStore.chapters" 
            @start="drag=true"
            @end="handleDragEnd"
            item-key="chapterTitle"
            handle=".drag-handle"
            :animation="200"
            class="chapter-list"
          >
            <template #item="{element: chapter, index}">
              <div class="section-level-1">
                <div 
                  :class="['section-title', { 'active': selectedSection === chapter.chapterTitle }]"
                  @click="selectSection(chapter.chapterTitle)"
                >
                  <div class="section-title-content">
                    <!-- 新增拖曳把手 -->
                    <div class="drag-handle">
                      <i class="mdi mdi-drag"></i>
                    </div>
                    <span style="width: 100%;">{{ getSectionNumber(index) }}. {{ chapter.chapterTitle }}</span>
                    <div class="section-actions">
                      <button 
                        class="edit-title-btn"
                        @click.stop="showEditTitleModal(chapter.chapterTitle, 'chapter')"
                        title="編輯標題"
                        style="display: none;"
                      >
                        <i class="mdi mdi-pencil"></i>
                      </button>
                      <button 
                        class="add-subsection-btn"
                        @click.stop="showAddSubsectionModal(chapter.chapterTitle)"
                        title="新增中章節"
                        style="display: none;"
                      >
                        <i class="mdi mdi-plus"></i>
                      </button>
                      <button 
                        class="delete-btn"
                        @click.stop="confirmDelete(chapter.chapterTitle, 'chapter')"
                        title="刪除"
                        style="display: none;"
                      >
                        <i class="mdi mdi-delete"></i>
                      </button>
                      <button 
                        class="toggle-btn"
                        @click.stop="toggleSection(chapter.chapterTitle)"
                        title="展開/收合"
                      >
                        <i :class="['mdi', isExpanded(chapter.chapterTitle) ? 'mdi-chevron-down' : 'mdi-chevron-right']"></i>
                      </button>
                    </div>
                  </div>
                </div>
                
                <!-- 中章節 -->
                <div v-if="isExpanded(chapter.chapterTitle)" class="sub-chapters">
                  <div 
                    v-for="(subChapter, subIndex) in chapter.subChapters" 
                    :key="subChapter.BlockID"
                    class="section-level-2"
                  >
                    <div 
                      :class="['section-title', { 'active': selectedSection === subChapter.BlockID }]"
                      @click="selectSection(subChapter.BlockID)"
                    >
                      <div class="section-title-content">
                        <span>{{ getAlphabetLabel(subIndex) }}. {{ subChapter.subChapterTitle }}</span>
                        <div class="section-actions">
                          <button 
                            class="edit-title-btn"
                            @click.stop="showEditTitleModal(subChapter.BlockID, 'subChapter')"
                            title="編輯標題"
                            style="display: none;"
                          >
                            <i class="mdi mdi-pencil"></i>
                          </button>
                          <button 
                            class="delete-btn"
                            @click.stop="confirmDelete(chapter.chapterTitle, 'subChapter', subChapter.subChapterTitle)"
                            title="刪除"
                            style="display: none;"
                          >
                            <i class="mdi mdi-delete"></i>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>
      </div>
    </div>

    <!-- 主要編輯區域 -->
    <div :class="['main-content', { 'expanded': isSidebarCollapsed }]">
      <div class="editor-header">
        <div class="header-content">
          <!-- <h2>{{ getCurrentSectionTitle() }}</h2> -->
          <div class="theme-toggle">
            <button @click="toggleTheme" class="theme-button">
              <i :class="['mdi', theme === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny']"></i>
            </button>
          </div>
        </div>
      </div>
      
      <div class="editor-content">
        <!-- 當選中大章節時顯示所有子章節 -->
        <div v-if="!isSubChapter(selectedSection) && selectedSection" class="chapter-content">
          <h2 class="chapter-title">{{ getChapterTitle(selectedSection) }}</h2>
          
          <div class="subchapters-container">
            <div 
              v-for="subChapter in getSubChapters(selectedSection)" 
              :key="subChapter.BlockID"
              class="subchapter-block"
            >
              <h3 class="subchapter-title">{{ subChapter.subChapterTitle }}</h3>
              <!-- 替換為自定義div内容展示 -->
              <div class="content-container">
                <div 
                  class="content-display" 
                  :class="{ 'expanded': expandedContents[subChapter.BlockID] }"
                >
                  <div class="content-text" v-html="formatContentWithParagraphs(sectionContents[subChapter.BlockID])"></div>
                </div>
                <!-- 展開/收起按鈕 -->
                <div class="expand-toggle">
                  <button 
                    class="expand-btn" 
                    @click="toggleContentExpand(subChapter.BlockID)"
                    v-if="shouldShowExpandButton(sectionContents[subChapter.BlockID])"
                  >
                    <i :class="['mdi', expandedContents[subChapter.BlockID] ? 'mdi-chevron-up' : 'mdi-chevron-down']"></i>
                    <span>{{ expandedContents[subChapter.BlockID] ? '收起' : '展開全部' }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 準則檢驗按鈕 -->
          <div class="criteria-check-container">
            <button 
              class="criteria-check-btn"
              @click="handleCriteriaCheck"
              :disabled="reportEditStore.loading.isGenerating"
              :class="{ 'disabled': reportEditStore.loading.isGenerating }"
            >
              <i class="mdi mdi-check-circle"></i>
              <span>準則檢驗</span>
            </button>
            <!-- 新增審核按鈕 -->
            <button class="review-btn" @click="handleReview">
              <i class="mdi mdi-file-document-check"></i>
              <span>章節審核</span>
            </button>
            <!-- 新增審核記錄按鈕 -->
            <button class="history-btn" @click="showReviewHistory">
              <i class="mdi mdi-history"></i>
              <span>審核記錄</span>
            </button>
          </div>

          <!-- 準則檢驗結果 -->
          <GuidelinesResult 
            v-if="currentChapter && currentChapter.guidelines" 
            :checkResults="currentChapter.guidelines"
          />
        </div>

        <!-- 當選中中章節時顯示單一編輯區域 -->
        <div v-else-if="isSubChapter(selectedSection)" class="input-area">
          <div class="content-wrapper">
            <!-- 新增工具欄 -->
            <div class="editor-toolbar">
              <div class="toolbar-title">
                <h3>{{ getCurrentSectionTitle() }}</h3>
              </div>
              <div class="toolbar-actions">
                <button 
                  class="toolbar-btn generate-text-btn" 
                  @click="handleGenerateText" 
                  :disabled="reportEditStore.loading.isGenerating"
                  :class="{ 'disabled': reportEditStore.loading.isGenerating }"
                  title="生成文字"
                >
                  <i class="mdi mdi-text"></i>
                  <span>生成文字</span>
                </button>
                <button 
                  class="toolbar-btn generate-image-btn" 
                  @click="handleGenerateImage" 
                  :disabled="reportEditStore.loading.isGenerating"
                  :class="{ 'disabled': reportEditStore.loading.isGenerating }"
                  title="生成圖片"
                >
                  <i class="mdi mdi-image"></i>
                  <span>生成圖片</span>
                </button>
                <button 
                  class="toolbar-btn upload-btn" 
                  @click="triggerImageUpload" 
                  title="上傳圖片"
                >
                  <i class="mdi mdi-image-plus"></i>
                  <span>上傳圖片</span>
                </button>
              </div>
            </div>

            <!-- 替換為可編輯的div元素 -->
            <div 
              class="editable-content" 
              contenteditable="true"
              :placeholder="'請輸入' + getCurrentSectionTitle() + '的內容...'"
              @input="handleEditableContentInput"
              ref="editableContent"
            ></div>
            
            <!-- 圖片上傳區域 -->
            <div class="image-upload-area">
              <input 
                type="file" 
                ref="imageInput"
                @change="handleImageUpload" 
                accept="image/*"
                multiple
                class="hidden"
              />
              
              <!-- 圖片預覽區域 -->
              <div v-if="currentImages.length > 0" class="image-preview-area">
                <div v-for="(image, index) in currentImages" :key="index" class="image-preview-item">
                  <img :src="image.url || image" :alt="image.title || '圖片 ' + (index + 1)" />
                  <div class="image-info">
                    <input 
                      v-model="image.title"
                      placeholder="輸入圖片標題"
                      class="image-title-input"
                      @input="updateImageInfo(index)"
                    />
                    <input 
                      v-model="image.subtitle"
                      placeholder="輸入圖片描述"
                      class="image-subtitle-input"
                      @input="updateImageInfo(index)"
                    />
                  </div>
                  <button class="remove-image-btn" @click="removeImage(index)">
                    <i class="mdi mdi-close"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- 註解按鈕 -->
            <button 
              class="add-comment-btn"
              @click="addComment(selectedSection)"
              v-if="!comments[selectedSection] || !showCommentPanel"
            >
              <i class="mdi mdi-comment-plus-outline"></i>
              <span>{{ comments[selectedSection] ? '查看註解' : '添加註解' }}</span>
            </button>

            <!-- 註解面板 -->
            <div v-if="comments[selectedSection]" class="comment-panel" :class="{ 'show': showCommentPanel }">
              <div class="comment-header">
                <h4>註解</h4>
                <div class="comment-actions">
                  <button 
                    class="status-btn"
                    :class="{ 'resolved': comments[selectedSection].status === 'resolved' }"
                    @click="updateCommentStatus(selectedSection, comments[selectedSection].status === 'resolved' ? 'unfinished' : 'resolved')"
                  >
                    <i class="mdi" :class="comments[selectedSection].status === 'resolved' ? 'mdi-check-circle' : 'mdi-circle-outline'"></i>
                    <span>{{ comments[selectedSection].status === 'resolved' ? '已解決' : '未完成' }}</span>
                  </button>
                  <button class="close-btn" @click="closeCommentPanel">
                    <i class="mdi mdi-close"></i>
                  </button>
                </div>
              </div>
              <div class="comment-body">
                <textarea
                  v-model="comments[selectedSection].content"
                  class="comment-textarea"
                  placeholder="請輸入註解內容..."
                  @input="updateCommentContent(selectedSection, $event.target.value)"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-edit-message">
          請選擇左側章節以進行編輯
        </div>
      </div>
    </div>
  </div>

  <!-- 新增中章節的彈出視窗 -->
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <h3>新增中章節</h3>
      <div class="modal-form">
        <input 
          v-model="newSubsectionTitle" 
          type="text" 
          placeholder="請輸入中章節名稱"
          @keyup.enter="addSubsection"
        >
        <div class="modal-buttons">
          <button @click="addSubsection" class="primary-btn">確認</button>
          <button @click="closeModal" class="secondary-btn">取消</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 編輯標題的彈出視窗 -->
  <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
    <div class="modal-content" @click.stop>
      <h3>編輯標題</h3>
      <div class="modal-form">
        <input 
          v-model="editingTitle" 
          type="text" 
          placeholder="請輸入標題名稱"
          @keyup.enter="updateSectionTitle"
        >
        <div class="modal-buttons">
          <button @click="updateSectionTitle" class="primary-btn">確認</button>
          <button @click="closeEditModal" class="secondary-btn">取消</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 新增大章節的彈出視窗 -->
  <div v-if="showMainSectionModal" class="modal-overlay" @click="closeMainSectionModal">
    <div class="modal-content" @click.stop>
      <h3>新增大章節</h3>
      <div class="modal-form">
        <input 
          v-model="newMainSectionTitle" 
          type="text" 
          placeholder="請輸入大章節名稱"
          @keyup.enter="addMainSection"
        >
        <div class="modal-buttons">
          <button @click="addMainSection" class="primary-btn">確認</button>
          <button @click="closeMainSectionModal" class="secondary-btn">取消</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 新增審核歷程對話框 -->
  <el-dialog
    v-model="reviewHistoryDialogVisible"
    title="審核歷程"
    width="50%"
    :destroy-on-close="true"
    class="review-history-dialog dark"
    style="--el-dialog-bg-color: #1E1E1E; --el-text-color-primary: #ffffff;"
  >
    <div class="review-history-content">
      <el-timeline>
        <el-timeline-item
          v-for="(history, index) in reviewHistory"
          :key="index"
          :type="getHistoryType(history.reviewAction)"
          :timestamp="formatDate(history.reviewedAt)"
        >
          <div class="history-item">
            <div class="history-header" :class="{ 'approved': history.reviewAction === 'approved', 'rejected': history.reviewAction === 'rejected' }">
              <div class="history-title">
                <el-icon :size="16" :color="history.reviewAction === 'approved' ? '#67C23A' : '#F56C6C'" class="status-icon">
                  <Check v-if="history.reviewAction === 'approved'" />
                  <Close v-else />
                </el-icon>
                <h4>{{ history.stageName }} - {{ history.reviewerName }}</h4>
              </div>
              <el-tag :type="getStatusType(history.reviewAction)" :effect="history.reviewAction === 'approved' ? 'dark' : 'light'">
                {{ history.reviewAction === 'approved' ? '通過' : '退回' }}
              </el-tag>
            </div>
            <p class="history-comment">{{ history.reviewComments }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, provide, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ReportEditNav from './ReportEditNav.vue'
import { useUserStore } from '@/stores/user'
import { useReportEditStore } from '@/stores/reportEdit'
import draggable from 'vuedraggable'
import { useToast } from 'vue-toastification'
import GuidelinesResult from './GuidelinesResult.vue'
import { ElMessage } from 'element-plus'

// 使用 router 和 route
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const reportEditStore = useReportEditStore()
const toast = useToast()

// 側邊欄狀態
const isSidebarCollapsed = ref(false)
const selectedSection = ref(null)
const previousSection = ref(null)
const theme = ref('dark')
const expandedSections = ref(new Set())

// 計算當前選中的章節
const currentChapter = computed(() => {
  if (!selectedSection.value) return null
  return reportEditStore.chapters.find(chapter => {
    return chapter.chapterTitle === selectedSection.value || 
           chapter.subChapters.some(sub => sub.BlockID === selectedSection.value)
  })
})

// 新增中章節相關的響應式變數
const showModal = ref(false)
const newSubsectionTitle = ref('')
const currentParentTitle = ref(null)

// 添加新的響應式變數
const showEditModal = ref(false)
const editingTitle = ref('')
const editingType = ref(null) // 'chapter' 或 'subChapter'
const editingId = ref(null)

// 新增大章節相關的響應式變數
const showMainSectionModal = ref(false)
const newMainSectionTitle = ref('')

// 章節內容和註解
const sectionContents = ref({})
const comments = ref({})
const showCommentPanel = ref(false)
const imageInput = ref(null)
const currentImages = ref([])

// 展開/折疊內容相關
const expandedContents = ref({})

// 審核歷程相關
const reviewHistoryDialogVisible = ref(false)
const reviewHistory = ref([])

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

// 獲取狀態類型
const getStatusType = (status) => {
  const statusMap = {
    approved: 'success',
    rejected: 'danger',
    reviewing: 'warning'
  }
  return statusMap[status] || 'info'
}

// 獲取歷程類型
const getHistoryType = (status) => {
  const typeMap = {
    approved: 'success',
    rejected: 'danger',
    reviewing: 'warning'
  }
  return typeMap[status] || 'info'
}

// 顯示審核歷程
const showReviewHistory = async () => {
  if (!currentChapter.value) {
    ElMessage.warning('請先選擇要查看的章節')
    return
  }

  try {
    // 先獲取 workflowInstanceID
    const workflowInstanceID = await reportEditStore.fetchWorkflowInstanceID(
      route.query.assetId,
      currentChapter.value.chapterTitle
    )

    if (!workflowInstanceID) {
      ElMessage.warning('尚未有審核記錄')
      return
    }

    // 獲取審核記錄
    const logs = await reportEditStore.fetchReviewLogs(workflowInstanceID)
    reviewHistory.value = logs
    reviewHistoryDialogVisible.value = true
  } catch (error) {
    console.error('獲取審核記錄失敗:', error)
    ElMessage.error('獲取審核記錄失敗')
  }
}

// 監聽選中的章節變化，更新圖片列表
watch(selectedSection, (newSection) => {
  if (newSection) {
    const content = reportEditStore.getSubChapterContent(newSection)
    currentImages.value = content.img_content_url || []
  } else {
    currentImages.value = []
  }
})

// 監聽選中的章節變化，更新文本內容
watch(selectedSection, (newSection) => {
  if (newSection) {
    if (isSubChapter(newSection)) {
      // 如果是中章節，載入單一章節內容
      const content = reportEditStore.getSubChapterContent(newSection)
      sectionContents.value[newSection] = content.text_content
    } else {
      // 如果是大章節，載入所有子章節的內容
      const subChapters = getSubChapters(newSection)
      subChapters.forEach(subChapter => {
        const content = reportEditStore.getSubChapterContent(subChapter.BlockID)
        sectionContents.value[subChapter.BlockID] = content.text_content
      })
    }
  }
})

// 拖曳相關狀態
const drag = ref(false)

// 方法
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
}

const selectSection = async (sectionId) => {
  if (selectedSection.value === sectionId) return;
  
  // 獲取上一個章節的標題和內容
  let previousTitle = '';
  let previousContent = '';
  let previousBlockId = '';
  if (previousSection.value) {
    previousTitle = isSubChapter(previousSection.value) 
      ? reportEditStore.chapters.find(c => c.subChapters.some(s => s.BlockID === previousSection.value))
          ?.subChapters.find(s => s.BlockID === previousSection.value)?.subChapterTitle
      : reportEditStore.chapters.find(c => c.chapterTitle === previousSection.value)?.chapterTitle;
    previousContent = sectionContents.value[previousSection.value] || '';
    previousBlockId = previousSection.value;
  }

  // 獲取新章節的標題
  let newTitle = isSubChapter(sectionId)
    ? reportEditStore.chapters.find(c => c.subChapters.some(s => s.BlockID === sectionId))
        ?.subChapters.find(s => s.BlockID === sectionId)?.subChapterTitle
    : reportEditStore.chapters.find(c => c.chapterTitle === sectionId)?.chapterTitle;

  // 如果存在上一個章節，則輸出切換訊息並更新內容
  if (previousSection.value && previousContent) {
    // console.log(`章節切換: ${previousTitle} -> ${newTitle}`);
    // console.log('原章節 BlockID:', previousBlockId);
    // console.log('原文內容:', previousContent);
    // console.log('User ID:', userStore.userID);
    
    try {
      await reportEditStore.updateReportBlockData(previousBlockId, userStore.userID);
    } catch (error) {
      console.error('更新章節內容時發生錯誤:', error);
      // 可以在這裡添加錯誤提示給用戶
    }
  }

  // 更新章節記錄
  previousSection.value = sectionId;
  selectedSection.value = sectionId;
}

// 判斷是否為中章節
const isSubChapter = (sectionId) => {
  for (const chapter of reportEditStore.chapters) {
    if (chapter.subChapters.some(sub => sub.BlockID === sectionId)) {
      return true
    }
  }
  return false
}

// 獲取當前章節標題
const getCurrentSectionTitle = () => {
  if (!selectedSection.value) return ''
  
  for (const chapter of reportEditStore.chapters) {
    const subChapter = chapter.subChapters.find(sub => sub.BlockID === selectedSection.value)
    if (subChapter) {
      return subChapter.subChapterTitle
    }
  }
  return ''
}

// 初始化展開狀態
const initializeExpandedSections = () => {
  reportEditStore.chapters.forEach(chapter => {
    expandedSections.value.add(chapter.chapterTitle)
  })
}

// 在組件掛載時初始化
onMounted(async () => {
  // 檢查 URL 參數
  const assetId = route.query.assetId
  if (!assetId) {
    // 如果沒有 assetId 參數，導向 home 頁面
    router.push('/home')
    return
  }

  // 設定 assetId
  reportEditStore.setAssetId(assetId)

  await userStore.initializeFromStorage()
  
  // 初始化報告書數據
  await reportEditStore.initializeDefaultChapters({
    organization_id: userStore.organizationID,
    asset_id: assetId
  })
  
  initializeExpandedSections()
})

const toggleSection = (chapterTitle) => {
  if (expandedSections.value.has(chapterTitle)) {
    expandedSections.value.delete(chapterTitle)
  } else {
    expandedSections.value.add(chapterTitle)
  }
  selectSection(chapterTitle)
}

const isExpanded = (chapterTitle) => {
  return expandedSections.value.has(chapterTitle)
}

// 主題切換
const handleThemeChange = (newTheme) => {
  theme.value = newTheme
}

// 字體大小切換
const handleFontSizeChange = (size) => {
  const fontSizes = {
    small: '14px',
    medium: '16px',
    large: '18px'
  }
  document.documentElement.style.setProperty('--editor-font-size', fontSizes[size])
}

// 顯示新增中章節的彈出視窗
const showAddSubsectionModal = (chapterTitle) => {
  currentParentTitle.value = chapterTitle
  showModal.value = true
  newSubsectionTitle.value = ''
}

// 關閉彈出視窗
const closeModal = () => {
  showModal.value = false
  newSubsectionTitle.value = ''
}

// 新增中章節
const addSubsection = () => {
  if (!newSubsectionTitle.value.trim()) {
    alert('請輸入中章節名稱')
    return
  }

  const success = reportEditStore.addSubChapter(
    currentParentTitle.value,
    newSubsectionTitle.value.trim()
  )

  if (success) {
    // console.log('新增中章節成功', currentParentTitle.value, newSubsectionTitle.value.trim())
    reportEditStore.addSubChapter_api(
      currentParentTitle.value,
      newSubsectionTitle.value.trim(),
      userStore.userID,
      userStore.organizationID
    )
    closeModal()
  } else {
    toast.error('已存在相同標題的中章節')
  }
}

// 顯示編輯標題的彈出視窗
const showEditTitleModal = (id, type) => {
  editingId.value = id
  editingType.value = type
  if (type === 'chapter') {
    editingTitle.value = id // 因為對於大章節，id 就是標題
  } else {
    // 尋找對應的中章節標題
    for (const chapter of reportEditStore.chapters) {
      const subChapter = chapter.subChapters.find(sub => sub.BlockID === id)
      if (subChapter) {
        editingTitle.value = subChapter.subChapterTitle
        break
      }
    }
  }
  showEditModal.value = true
}

// 更新標題
const updateSectionTitle = () => {
  if (!editingTitle.value.trim()) {
    alert('請輸入標題名稱')
    return
  }

  if (editingType.value === 'chapter') {
    // 檢查是否已存在相同標題的大章節
    if (!reportEditStore.chapters.some(chapter => chapter.chapterTitle === editingTitle.value.trim())) {
      // 更新大章節標題
      const index = reportEditStore.chapters.findIndex(c => c.chapterTitle === editingId.value)
      if (index !== -1) {
        reportEditStore.chapters[index].chapterTitle = editingTitle.value.trim()
        reportEditStore.updateReportOutlineRenameChapterTitle(editingId.value, editingTitle.value.trim())
      }
    } else {
      toast.error('已存在相同標題的大章節')
    }
  } else {
    // 檢查是否已存在相同標題的中章節
    let titleExists = false
    for (const chapter of reportEditStore.chapters) {
      if (chapter.subChapters.some(sub => sub.subChapterTitle === editingTitle.value.trim())) {
        titleExists = true
        break
      }
    }

    if (!titleExists) {
      // 更新中章節標題
      for (const chapter of reportEditStore.chapters) {
        const subChapter = chapter.subChapters.find(sub => sub.BlockID === editingId.value)
        if (subChapter) {
          // console.log('更新中章節標題成功', chapter.chapterTitle, subChapter.subChapterTitle, editingTitle.value.trim())
          reportEditStore.updateReportOutlineRenameSubChapterTitle(chapter.chapterTitle, subChapter.subChapterTitle, editingTitle.value.trim())
          subChapter.subChapterTitle = editingTitle.value.trim()
          break
        }
      }
    } else {
      toast.error('已存在相同標題的中章節')
    }
  }
  closeEditModal()
}

// 關閉編輯模態框
const closeEditModal = () => {
  showEditModal.value = false
  editingTitle.value = ''
  editingId.value = null
  editingType.value = null
}

// 新增：關閉註解面板的方法
const closeCommentPanel = () => {
  showCommentPanel.value = false
}

// 刪除章節
const confirmDelete = (title, type, subTitle = null) => {
  const message = type === 'chapter' 
    ? `確定要刪除「${title}」章節及其所有子章節嗎？` 
    : `確定要刪除「${subTitle}」章節嗎？`

  if (confirm(message)) {
    if (type === 'chapter') {
      reportEditStore.removeChapter(title)
    } else {
      reportEditStore.removeSubChapter(title, subTitle)
    }
  }
}

// 顯示新增大章節的彈出視窗
const showAddMainSectionModal = () => {
  showMainSectionModal.value = true
  newMainSectionTitle.value = ''
}

// 關閉新增大章節的彈出視窗
const closeMainSectionModal = () => {
  showMainSectionModal.value = false
  newMainSectionTitle.value = ''
}

// 新增大章節
const addMainSection = () => {
  if (!newMainSectionTitle.value.trim()) {
    toast.error('請輸入大章節名稱')
    return
  }

  const success = reportEditStore.addChapter(newMainSectionTitle.value.trim())
  if (!success) {
    toast.error('已存在相同標題的大章節')
    return
  }
  reportEditStore.updateReportOutline()
  closeMainSectionModal()
}

// 生成章節序號的方法
const getSectionNumber = (index) => {
  return index + 1
}

// 輔助函數：將數字轉換為字母標籤 (A, B, C...)
const getAlphabetLabel = (index) => {
  return String.fromCharCode(65 + index)
}

// 提供儲存方法給子組件
const handleSave = () => {
  // 在這裡實現儲存邏輯
  console.log('儲存內容：', {
    fileName: reportEditStore.fileName,
    chapters: reportEditStore.chapters,
    contents: sectionContents.value,
    comments: comments.value
  })
  return true
}

provide('handleSave', handleSave)

// 處理內容變化
const handleContentChange = (blockId = null) => {
  const targetBlockId = blockId || selectedSection.value
  if (targetBlockId) {
    reportEditStore.updateSubChapterText(
      targetBlockId, 
      sectionContents.value[targetBlockId]
    )
  }
}

// 觸發圖片上傳
const triggerImageUpload = () => {
  imageInput.value.click()
}

// 處理圖片上傳
const handleImageUpload = (event) => {
  const files = event.target.files
  if (!files.length) return

  Array.from(files).forEach(file => {
    const reader = new FileReader()
    reader.onload = async (e) => {
      const newImage = {
        url: e.target.result,
        title: '',
        subtitle: ''
      }
      currentImages.value.push(newImage)
      await reportEditStore.updateSubChapterImages(selectedSection.value, currentImages.value)
    }
    reader.readAsDataURL(file)
  })
  
  // 清空 input，以便可以重複上傳相同的圖片
  event.target.value = ''
}

// 更新圖片訊息
const updateImageInfo = async (index) => {
  await reportEditStore.updateSubChapterImages(selectedSection.value, currentImages.value)
}

// 移除圖片
const removeImage = async (index) => {
  currentImages.value.splice(index, 1)
  await reportEditStore.updateSubChapterImages(selectedSection.value, currentImages.value)
}

// 獲取大章節標題
const getChapterTitle = (chapterTitle) => {
  const chapter = reportEditStore.chapters.find(c => c.chapterTitle === chapterTitle)
  return chapter ? chapter.chapterTitle : ''
}

// 獲取大章節下的所有中章節
const getSubChapters = (chapterTitle) => {
  const chapter = reportEditStore.chapters.find(c => c.chapterTitle === chapterTitle)
  return chapter ? chapter.subChapters : []
}

// 處理準則檢驗按鈕點擊
const handleCriteriaCheck = () => {
  if (currentChapter.value) {
    // 遍歷所有中章節並輸出內容
    let outputContent = `標題：${currentChapter.value.chapterTitle}\n\n\n`
    currentChapter.value.subChapters.forEach(sub => {
      outputContent += `章節：${sub.subChapterTitle}\n` +
        `內容：\n\`\`\`\n${sub.text_content}\`\`\`\n\n`
    })
    
    reportEditStore.verification_criteria_by_chapter(currentChapter.value.chapterTitle, outputContent)
      .then(response => {
        if (response.status === 'success') {
          toast.success('準則檢驗完成')
        }
      })
      .catch(error => {
        toast.error('準則檢驗失敗：' + error.message)
      })
  } else {
    toast.error('請先選擇要檢驗的章節')
  }
}

// 處理審核按鈕點擊
const handleReview = () => {
  if (currentChapter.value) {
    // console.log(`大章節：${currentChapter.value.chapterTitle} 呼叫審核按鈕`)
    reportEditStore.workflow_instance(route.query.assetId, userStore.organizationID, userStore.userID, currentChapter.value.chapterTitle)
  }
}

// 拖曳結束
const handleDragEnd = async (evt) => {
  drag.value = false
  const movedItem = evt.item.__draggable_context.element
  // console.log('完成拖移章節:', movedItem.chapterTitle)
  // 更新報告書大綱
  await reportEditStore.updateReportOutline()
}

// 處理生成文字按鈕點擊
const handleGenerateText = async () => {
  // 獲取當前選中的章節信息
  const currentChapter = reportEditStore.chapters.find(chapter => {
    return chapter.subChapters.some(sub => sub.BlockID === selectedSection.value) ||
           chapter.chapterTitle === selectedSection.value
  })

  if (currentChapter) {
    const chapterTitle = currentChapter.chapterTitle
    let subChapterTitle = ''
    let content = ''

    if (isSubChapter(selectedSection.value)) {
      const subChapter = currentChapter.subChapters.find(sub => sub.BlockID === selectedSection.value)
      if (subChapter) {
        subChapterTitle = subChapter.subChapterTitle
        content = sectionContents.value[selectedSection.value] || ''
      }
    }

    // console.log(`大章節: ${chapterTitle}, 中章節: ${subChapterTitle}, 文字內容: ${content}, 呼叫生成文字`)
    const responseData = await reportEditStore.generateText(chapterTitle, subChapterTitle)
    console.log('生成文字結果:', responseData)
    sectionContents.value[selectedSection.value] = responseData.text
    reportEditStore.updateSubChapterText(selectedSection.value, responseData.text)
    // console.log('生成文字結果:', text)
  }
}

// 處理生成圖片按鈕點擊
const handleGenerateImage = async () => {
  try {
    // 獲取當前選中的章節信息
    const currentChapter = reportEditStore.chapters.find(chapter => {
      return chapter.subChapters.some(sub => sub.BlockID === selectedSection.value) ||
             chapter.chapterTitle === selectedSection.value
    })

    if (currentChapter) {
      const chapterTitle = currentChapter.chapterTitle
      let subChapterTitle = ''
      let content = ''

      if (isSubChapter(selectedSection.value)) {
        const subChapter = currentChapter.subChapters.find(sub => sub.BlockID === selectedSection.value)
        if (subChapter) {
          subChapterTitle = subChapter.subChapterTitle
          content = sectionContents.value[selectedSection.value] || ''
        }
      }

      if (!content.trim()) {
        ElMessage.warning('請先輸入要生成圖表的文字內容')
        return
      }

      console.log(`大章節: ${chapterTitle}, 中章節: ${subChapterTitle}, 文字內容: ${content}, 呼叫生成圖片`)
      
      // 調用生成圖片 API
      const result = await reportEditStore.generateMermaidImage(content)
      if (result && result.image_url) {
        // 構建完整的圖片對象
        const newImage = {
          url: result.image_url,
          title: '生成的圖表',
          subtitle: '由 Mermaid 自動生成'
        }
        
        // 更新當前圖片列表
        currentImages.value = [...currentImages.value, newImage]
        
        // 更新 store 中的圖片列表
        await reportEditStore.updateSubChapterImages(selectedSection.value, currentImages.value)
        
        // 提示用戶生成成功
        ElMessage.success('圖片生成成功')
      }
    }
  } catch (error) {
    console.error('生成圖片時發生錯誤:', error)
    ElMessage.error('生成圖片失敗: ' + error.message)
  }
}

// 添加計算屬性
const getLoadingMessage = computed(() => {
  switch (reportEditStore.loading.currentAction) {
    case 'generateText':
      return '正在生成文字，請稍後...'
    case 'generateImage':
      return '正在生成圖片，請稍後...'
    case 'criteriaCheck':
      return '正在進行準則檢驗，請稍後...'
    default:
      return '處理中，請稍後...'
  }
})

// 格式化內容，添加段落分隔
const formatContentWithParagraphs = (content) => {
  if (!content) return ''
  // 將文本內容按段落分隔並添加樣式
  return content
    .split('\n')
    .map(paragraph => paragraph.trim())
    .filter(paragraph => paragraph.length > 0)
    .map(paragraph => `<p class="content-paragraph">${paragraph}</p>`)
    .join('')
}

// 判斷是否顯示展開按鈕
const shouldShowExpandButton = (content) => {
  if (!content) return false
  // 根據內容長度或行數決定是否顯示展開按鈕
  const lines = content.split('\n').filter(line => line.trim().length > 0)
  return lines.length > 5 || content.length > 500
}

// 切換內容展開/折疊狀態
const toggleContentExpand = (blockId) => {
  expandedContents.value[blockId] = !expandedContents.value[blockId]
}

// 處理可編輯內容的輸入事件
const handleEditableContentInput = (event) => {
  sectionContents.value[selectedSection.value] = event.target.innerHTML
  handleContentChange(selectedSection.value)
}

// 監聽選中的章節變化，更新可編輯div的內容
watch(selectedSection, (newSection) => {
  if (newSection) {
    nextTick(() => {
      const editableContentElement = document.querySelector('.editable-content')
      if (editableContentElement && isSubChapter(newSection)) {
        // 轉換存儲的內容為HTML格式
        const formattedContent = formatContentToHtml(sectionContents.value[newSection] || '')
        editableContentElement.innerHTML = formattedContent
      }
    })
  }
})

// 將純文本內容轉換為HTML
const formatContentToHtml = (content) => {
  if (!content) return ''
  
  // 如果內容已經是HTML，直接返回
  if (content.includes('<p') || content.includes('<div')) {
    return content
  }
  
  // 將純文本轉換為段落
  return content
    .split('\n')
    .map(paragraph => paragraph.trim())
    .filter(paragraph => paragraph.length > 0)
    .map(paragraph => `<p>${paragraph}</p>`)
    .join('')
}
</script>

<style scoped>
.editor-container {
  display: flex;
  height: 100vh;
  transition: all 0.3s ease;
  background-color: #ffffff;
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  padding-top: 60px; /* 為頂部導航欄留出空間 */
  font-size: var(--editor-font-size, 16px);
}

.editor-container.dark {
  background-color: #1a1a1a;
}

.sidebar-wrapper {
  position: relative;
  z-index: 2;
}

.sidebar {
  height: calc(100vh - 60px);
  width: 300px;
  transition: all 0.3s ease;
  position: fixed;
  background-color: #f8f9fa;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
  top: 60px;
}

.dark .sidebar {
  background-color: #1a1a1a;
  border-right: 1px solid #2d2d2d;
}

.sidebar.collapsed {
  width: 0;
  padding: 0;
  border-right: none;
}

.sidebar-content,
.sidebar-header h3 {
  opacity: 1;
  visibility: visible;
  transition: opacity 0.2s ease;
  transition-delay: 0.2s;
  min-width: 280px;
}

.sidebar.collapsed .sidebar-content,
.sidebar.collapsed .sidebar-header h3 {
  opacity: 0;
  visibility: hidden;
  transition-delay: 0s;
}

.sidebar-header {
  height: 60px;
  padding: 0 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  border-bottom: 1px solid #e2e8f0;
  min-width: 280px;
  overflow: hidden;
}

.dark .sidebar-header {
  border-bottom: 1px solid #2d2d2d;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  white-space: nowrap;
}

.dark .sidebar-header h3 {
  color: #ffffff;
}

.sidebar-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: fixed;
  left: 268px;
  top: 30px;
  transform: translateY(-50%);
  z-index: 1000;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.dark .sidebar-toggle {
  background-color: #ffffff;
  border: 1px solid #404040;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.sidebar-toggle:hover {
  transform: translateY(-50%) scale(1.1);
}

.section-level-1 {
  margin-bottom: 0.5rem;
  padding: 0 1rem;
}

.section-level-2 {
  padding-left: 1.5rem;
  margin-top: 0.25rem;
}

.section-level-3 {
  padding-left: 1.5rem;
  margin-top: 0.25rem;
}

.section-title {
  padding: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.section-title:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .section-title:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.section-title.active {
  background-color: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}

.dark .section-title.active {
  background-color: rgba(96, 165, 250, 0.1);
  color: #60a5fa;
}

.light .section-level-1 > .section-title {
  font-weight: 600;
  color: #1a1a1a;
}

.dark .section-level-1 > .section-title {
  font-weight: 600;
  color: #ffffff;
}

.light .section-level-2 > .section-title {
  font-weight: 500;
  color: #2d3748;
}

.dark .section-level-2 > .section-title {
  font-weight: 500;
  color: #e2e8f0;
}

.light .section-level-3 > .section-title {
  font-weight: 400;
  color: #4a5568;
}

.dark .section-level-3 > .section-title {
  font-weight: 400;
  color: #cbd5e0;
}

.light .section-title {
  color: #000000;
}

.dark .section-title {
  color: #ffffff;
}

.light .section-title:hover {
  background-color: #e2e8f0;
}

.light .section-title.active {
  background-color: #e2e8f0;
  color: #2563eb;
}

.dark .section-title:hover {
  background-color: #2d2d2d;
}

.dark .section-title.active {
  background-color: #2d2d2d;
  color: #60a5fa;
}

.main-content {
  flex: 1;
  padding: 2rem 2rem 2rem 3rem;
  transition: all 0.3s ease;
  margin-left: 280px;
  height: calc(100vh - 60px);
  overflow-y: auto;
  position: relative;
}

.main-content.expanded {
  margin-left: 0;
}

.light .main-content {
  background-color: #ffffff;
  color: #000000;
}

.dark .main-content {
  background-color: #1a1a1a;
  color: #ffffff;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.light .header-content {
  color: #000000;
}

.dark .header-content {
  color: #ffffff;
}

.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-button {
  /* 因為 navbar 已經有主題切換按鈕，所以這裡不需要再顯示 */
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.light .theme-button {
  color: #4b5563;
}

.dark .theme-button {
  color: #ffffff;
}

.theme-button:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .theme-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.tiptap-editor {
  border-radius: 8px;
  min-height: 300px;
  padding: 1rem;
}

.light .tiptap-editor {
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  color: #000000;
}

.dark .tiptap-editor {
  border: 1px solid #2d2d2d;
  background-color: #1a1a1a;
  color: #e2e8f0;
}

.dark .tiptap-editor p {
  color: #e2e8f0;
}

.dark .tiptap-editor * {
  color: #e2e8f0;
}

.mdi {
  line-height: 1;
  vertical-align: middle;
  font-size: 1.2rem;
}

.light h2 {
  color: #000000;
}

.dark h2 {
  color: #ffffff;
}

.sidebar.collapsed + .main-content {
  margin-left: 0;
}

.sidebar.collapsed .sidebar-toggle {
  left: 0;
}

.section-title-content {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 0.5rem;
}

.section-title-content i {
  font-size: 1rem;
  transition: transform 0.3s ease;
}

.hidden {
  display: none;
}

.content-textarea {
  width: 100%;
  min-height: 300px;
  padding: 1rem;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
  font-size: var(--editor-font-size, 16px);
}

.light .content-textarea {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  color: #000000;
}

.dark .content-textarea {
  background-color: #1a1a1a;
  border: 1px solid #2d2d2d;
  color: #ffffff;
}

.no-edit-message {
  text-align: center;
  padding: 2rem;
  color: #666;
  font-style: italic;
}

.dark .no-edit-message {
  color: #999;
}

.input-area {
  margin-top: 1rem;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-subsection-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s ease;
}

.section-title:hover .add-subsection-btn {
  opacity: 1;
}

.light .add-subsection-btn {
  color: #4b5563;
}

.dark .add-subsection-btn {
  color: #e2e8f0;
}

.add-subsection-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .add-subsection-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.light .modal-content {
  background-color: #ffffff;
  color: #1a1a1a;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dark .modal-content {
  background-color: #1a1a1a;
  color: #ffffff;
  border: 1px solid #2d2d2d;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.modal-content {
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
}

.light .modal-content h3 {
  color: #1a1a1a;
}

.dark .modal-content h3 {
  color: #ffffff;
}

.modal-content h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.light .modal-form input {
  background-color: #ffffff;
  color: #1a1a1a;
  border: 1px solid #e2e8f0;
}

.dark .modal-form input {
  background-color: #2d2d2d;
  color: #ffffff;
  border-color: #404040;
}

.modal-form input {
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.light .modal-form input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.dark .modal-form input:focus {
  border-color: #60a5fa;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1);
}

.modal-form input:focus {
  outline: none;
}

.modal-buttons {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.primary-btn,
.secondary-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  border: none;
  font-weight: 500;
  transition: all 0.2s ease;
}

.primary-btn {
  background-color: #2563eb;
  color: #ffffff;
}

.primary-btn:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
}

.primary-btn:active {
  transform: translateY(0);
}

.light .secondary-btn {
  background-color: #e2e8f0;
  color: #1a1a1a;
  border: none;
}

.dark .secondary-btn {
  background-color: #2d2d2d;
  color: #ffffff;
  border: 1px solid #404040;
}

.light .secondary-btn:hover {
  background-color: #cbd5e0;
}

.dark .secondary-btn:hover {
  background-color: #404040;
}

.secondary-btn:hover {
  transform: translateY(-1px);
}

.secondary-btn:active {
  transform: translateY(0);
}

.light .modal-form input::placeholder {
  color: #9ca3af;
}

.dark .modal-form input::placeholder {
  color: #6b7280;
}

.edit-title-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s ease;
}

.section-title:hover .edit-title-btn {
  opacity: 1;
}

.light .edit-title-btn {
  color: #4b5563;
}

.dark .edit-title-btn {
  color: #e2e8f0;
}

.edit-title-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .edit-title-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.content-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-upload-area {
  padding: 1rem;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-upload-buttons {
  display: none;
}

.image-preview-area {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
  width: 100%;
}

.image-preview-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.image-preview-item img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  background-color: #f8f9fa;
}

.dark .image-preview-item img {
  background-color: #2d2d2d;
}

.image-info {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.image-title-input,
.image-subtitle-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 0.875rem;
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: all 0.2s ease;
}

.image-title-input:focus,
.image-subtitle-input:focus {
  outline: none;
  border-color: #2563eb;
}

.dark .image-title-input:focus,
.dark .image-subtitle-input:focus {
  border-color: #3b82f6;
}

.remove-image-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  backdrop-filter: blur(4px);
}

.remove-image-btn:hover {
  background-color: rgba(220, 38, 38, 0.8);
  transform: scale(1.1);
}

.dark .remove-image-btn {
  background-color: rgba(255, 255, 255, 0.2);
}

.dark .remove-image-btn:hover {
  background-color: rgba(239, 68, 68, 0.8);
}

.add-comment-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  /* 暫時關閉註解功能 */
  /* display: flex; */
  display: none;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
  opacity: 0;
  z-index: 999; /* 確保按鈕在適當的層級 */
}

.content-wrapper:hover .add-comment-btn {
  opacity: 1;
}

.add-comment-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .add-comment-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.comment-panel {
  position: fixed;
  top: 60px;
  right: -300px; /* 初始位置在視窗外 */
  width: 300px;
  height: calc(100vh - 60px);
  background-color: var(--bg-color);
  border-left: 1px solid var(--border-color);
  transition: right 0.3s ease;
  z-index: 1000;
}

.comment-panel.show {
  right: 0;
}

.dark .comment-panel {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.comment-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comment-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}

.comment-actions {
  display: flex;
  gap: 0.5rem;
}

.status-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.status-btn.resolved {
  background-color: #059669;
  color: white;
  border-color: #059669;
}

.close-btn {
  padding: 0.25rem;
  border: none;
  background: none;
  color: var(--text-color);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .close-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.comment-body {
  padding: 1rem;
}

.comment-textarea {
  width: 100%;
  min-height: 100px;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--bg-color);
  color: var(--text-color);
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
}

.comment-textarea:focus {
  outline: none;
  border-color: #2563eb;
}

.dark .comment-textarea:focus {
  border-color: #60a5fa;
}

.delete-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s ease;
  color: #dc2626;
}

.section-title:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background-color: rgba(220, 38, 38, 0.1);
}

.dark .delete-btn {
  color: #ef4444;
}

.dark .delete-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

/* 添加新的樣式 */
.add-main-section {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.add-main-section-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  background: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.light .add-main-section-btn {
  border-color: #e2e8f0;
  color: #4b5563;
}

.dark .add-main-section-btn {
  border-color: #2d2d2d;
  color: #e2e8f0;
}

.add-main-section-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.add-main-section-btn i {
  font-size: 1.2rem;
}

/* 確保 modal 樣式與其他 modal 一致 */
.modal-overlay {
  z-index: 1001;
}

/* 拖曳相關樣式 */
.drag-handle {
  display: flex;
  align-items: center;
  cursor: move;
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #666;
}

.dark .drag-handle {
  color: #999;
}

.section-title:hover .drag-handle {
  opacity: 0.5;
}

.section-title:hover .drag-handle:hover {
  opacity: 1;
}

/* 拖曳時的樣式 */
.sortable-ghost {
  opacity: 0.5;
  background-color: #e2e8f0;
}

.dark .sortable-ghost {
  background-color: #2d2d2d;
}

.sortable-drag {
  background-color: #f8f9fa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.dark .sortable-drag {
  background-color: #1a1a1a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* 新增樣式 */
.chapter-list {
  padding: 0.5rem 0;
}

.sub-chapters {
  padding-left: 1.5rem;
}

/* 新增樣式 */
.chapter-content {
  padding: 2rem;
}

.chapter-title {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 2rem;
  color: var(--text-color);
}

.subchapters-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.subchapter-block {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.dark .subchapter-block {
  background-color: #2d2d2d;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.subchapter-title {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: 1rem;
  color: var(--text-color);
}

.criteria-check-container {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  gap: 1rem; /* 添加按鈕之間的間距 */
}

.criteria-check-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  background-color: #2563eb;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.criteria-check-btn:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
}

.criteria-check-btn:active {
  transform: translateY(0);
}

.dark .criteria-check-btn {
  background-color: #3b82f6;
}

.dark .criteria-check-btn:hover {
  background-color: #2563eb;
}

/* 確保文字框樣式一致 */
.subchapter-block .content-textarea {
  width: 100%;
  min-height: 200px;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background-color: #ffffff;
  color: #000000;
  font-size: var(--editor-font-size, 16px);
  line-height: 1.5;
  resize: vertical;
}

.dark .subchapter-block .content-textarea {
  background-color: #1a1a1a;
  border-color: #2d2d2d;
  color: #ffffff;
}

.subchapter-block .content-textarea:focus {
  outline: none;
  border-color: #2563eb;
}

.dark .subchapter-block .content-textarea:focus {
  border-color: #3b82f6;
}

/* 新增展開/收合按鈕樣式 */
.toggle-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: inherit;
}

.toggle-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.toggle-btn i {
  font-size: 1.2rem;
}

.upload-btn,
.generate-text-btn,
.generate-image-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  color: white;
}

.upload-btn {
  background-color: #2563eb;
}

.generate-text-btn {
  background-color: #10b981;
}

.generate-image-btn {
  background-color: #8b5cf6;
}

.dark .upload-btn {
  background-color: #3b82f6;
}

.dark .generate-text-btn {
  background-color: #34d399;
}

.dark .generate-image-btn {
  background-color: #a78bfa;
}

/* 新增工具欄樣式 */
.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  border-bottom: none;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  backdrop-filter: blur(8px);
}

.dark .editor-toolbar {
  background-color: rgba(45, 45, 45, 0.95);
}

.toolbar-title h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--text-color);
}

.toolbar-actions {
  display: flex;
  gap: 0.5rem;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
}

.toolbar-btn:hover {
  transform: translateY(-1px);
}

.toolbar-btn:active {
  transform: translateY(0);
}

/* 調整文本區域樣式以配合工具欄 */
.content-textarea {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

/* 修改原有按鈕樣式 */
.upload-btn,
.generate-text-btn,
.generate-image-btn {
  background-color: var(--primary-color);
}

.upload-btn {
  background-color: #2563eb;
}

.generate-text-btn {
  background-color: #10b981;
}

.generate-image-btn {
  background-color: #8b5cf6;
}

.dark .upload-btn {
  background-color: #3b82f6;
}

.dark .generate-text-btn {
  background-color: #34d399;
}

.dark .generate-image-btn {
  background-color: #a78bfa;
}

/* 移除原有的圖片上傳區域按鈕 */
.image-upload-buttons {
  display: none;
}

/* 新增審核按鈕樣式 */
.review-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  background-color: #059669;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.review-btn:hover {
  background-color: #047857;
  transform: translateY(-1px);
}

.review-btn:active {
  transform: translateY(0);
}

.dark .review-btn {
  background-color: #10b981;
}

.dark .review-btn:hover {
  background-color: #059669;
}

/* 添加 loading 提示訊息樣式 */
.loading-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 9999;
  animation: slideIn 0.3s ease;
  backdrop-filter: blur(4px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dark .loading-message {
  background-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.loading-message i {
  font-size: 20px;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 添加旋轉動畫 */
.mdi-spin {
  animation: spin 1s infinite linear;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 添加禁用狀態樣式 */
.toolbar-btn.disabled,
.criteria-check-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  pointer-events: none;
}

.dark .toolbar-btn.disabled,
.dark .criteria-check-btn.disabled {
  opacity: 0.5;
}

/* 修改按鈕 hover 效果 */
.toolbar-btn:not(.disabled):hover,
.criteria-check-btn:not(.disabled):hover {
  transform: translateY(-1px);
}

.toolbar-btn:not(.disabled):active,
.criteria-check-btn:not(.disabled):active {
  transform: translateY(0);
}

/* 添加禁用時的過渡效果 */
.toolbar-btn,
.criteria-check-btn {
  transition: all 0.3s ease, opacity 0.2s ease;
}

/* 添加禁用時的視覺反饋 */
.toolbar-btn.disabled::after,
.criteria-check-btn.disabled::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: inherit;
  pointer-events: none;
}

/* 確保按鈕內容在禁用時保持清晰 */
.toolbar-btn.disabled i,
.toolbar-btn.disabled span,
.criteria-check-btn.disabled i,
.criteria-check-btn.disabled span {
  opacity: 0.8;
}

/* 審核歷程對話框樣式 */
.review-history-dialog :deep(.el-dialog) {
  background-color: #1E1E1E;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.review-history-dialog :deep(.el-dialog__title) {
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 600;
}

.review-history-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #FFFFFF;
}

.review-history-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  margin: 0;
  border-bottom: 1px solid #333333;
}

.review-history-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
  background-color: #1E1E1E;
}

.review-history-content::-webkit-scrollbar {
  width: 6px;
}

.review-history-content::-webkit-scrollbar-thumb {
  background-color: #4A5568;
  border-radius: 3px;
}

.review-history-content::-webkit-scrollbar-track {
  background-color: #2D3748;
}

.history-item {
  padding: 16px;
  background-color: #2D3748;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid #3D4A5C;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  margin: -8px -12px 12px;
  transition: background-color 0.3s ease;
}

.history-header.approved {
  background-color: rgba(103, 194, 58, 0.15);
}

.history-header.rejected {
  background-color: rgba(245, 108, 108, 0.15);
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
}

.history-header h4 {
  margin: 0;
  color: #E2E8F0;
  font-size: 14px;
  font-weight: 500;
}

.history-comment {
  color: #CBD5E0;
  margin: 12px 0 4px;
  font-size: 14px;
  line-height: 1.6;
  padding: 0 4px;
}

:deep(.el-timeline) {
  padding: 0 8px;
}

:deep(.el-timeline-item__node) {
  background-color: #4A5568;
  border-color: #2D3748;
  width: 12px;
  height: 12px;
}

:deep(.el-timeline-item__tail) {
  border-left-color: #4A5568;
}

:deep(.el-timeline-item__wrapper) {
  padding-left: 28px;
}

:deep(.el-timeline-item__content) {
  color: #E2E8F0;
}

:deep(.el-timeline-item__timestamp) {
  color: #A0AEC0;
  font-size: 12px;
  padding-top: 8px;
}

:deep(.el-tag) {
  border: none;
  padding: 4px 12px;
  height: 24px;
  line-height: 16px;
  font-size: 12px;
  font-weight: 500;
}

:deep(.el-tag--success) {
  background-color: rgba(103, 194, 58, 0.2);
  color: #67C23A;
}

:deep(.el-tag--danger) {
  background-color: rgba(245, 108, 108, 0.2);
  color: #F56C6C;
}

:deep(.el-tag--warning) {
  background-color: rgba(230, 162, 60, 0.2);
  color: #E6A23C;
}

/* 新增審核記錄按鈕樣式 */
.history-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  background-color: #6a7b9a;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-btn:hover {
  background-color: #2D3748;
  transform: translateY(-1px);
}

.history-btn:active {
  transform: translateY(0);
}

.dark .history-btn {
  background-color: #4A5568;
}

.dark .history-btn:hover {
  background-color: #2D3748;
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.content-display {
  max-height: 200px;
  overflow: hidden;
  transition: max-height 0.5s ease;
  background-color: var(--bg-color-light);
  border-radius: 6px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.content-display.expanded {
  max-height: 2000px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

.content-paragraph {
  margin-bottom: 0.8rem;
  position: relative;
  padding-bottom: 0.8rem;
}

.content-paragraph:not(:last-child)::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.1);
}

.expand-toggle {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-color);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  background-color: var(--bg-color-light);
  font-size: 0.9rem;
}

.expand-btn:hover {
  color: #2563eb;
  background-color: var(--bg-color-hover);
}

.expand-btn:active {
  transform: translateY(1px);
}

.dark .content-display {
  background-color: #2D3748;
}

.dark .expand-btn {
  background-color: #2D3748;
}

.dark .expand-btn:hover {
  background-color: #3A4A5E;
}

.light .content-display {
  background-color: #F7FAFC;
}

.light .expand-btn {
  background-color: #F7FAFC;
}

.light .expand-btn:hover {
  background-color: #EDF2F7;
}

.light .content-paragraph:not(:last-child)::after {
  background-color: rgba(0, 0, 0, 0.1);
}

.editable-content {
  width: 100%;
  min-height: 300px;
  padding: 1rem;
  border-radius: 8px;
  font-family: inherit;
  line-height: 1.5;
  font-size: var(--editor-font-size, 16px);
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  color: #000000;
  position: relative;
  transition: all 0.2s;
  overflow-y: auto;
  white-space: pre-wrap;
}

.editable-content:empty:before {
  content: attr(placeholder);
  position: absolute;
  top: 1rem;
  left: 1rem;
  color: #a0aec0;
  pointer-events: none;
}

.editable-content:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.editable-content p {
  margin-bottom: 0.8rem;
  position: relative;
  padding-bottom: 0.8rem;
}

.editable-content p:not(:last-child)::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .editable-content {
  background-color: #1a1a1a;
  border-color: #2d2d2d;
  color: #ffffff;
}

.dark .editable-content:empty:before {
  color: #718096;
}

.dark .editable-content:focus {
  border-color: #60a5fa;
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2);
}

.dark .editable-content p:not(:last-child)::after {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>