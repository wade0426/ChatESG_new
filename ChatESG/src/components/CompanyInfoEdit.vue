<!-- **公司基本資料編輯頁面 (CompanyInfoEdit.vue)** -->

<template>
  <!-- <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
  <Header @openNav="openNav" /> -->

  <div :class="['editor-container', theme]">
    <!-- 引入頂部導航欄 -->
    <CompanyInfoEditNav 
      @toggle-sidebar="toggleSidebar" 
      @theme-change="handleThemeChange"
      @font-size-change="handleFontSizeChange" 
    />
    
    <!-- 側邊欄 -->
    <div class="sidebar-wrapper">
      <div :class="['sidebar', { 'collapsed': isSidebarCollapsed }]">
        <div class="sidebar-header">
          <h3>公司基本資料表</h3>
          <button @click="toggleSidebar" class="sidebar-toggle">
            <i :class="['mdi', isSidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left']"></i>
          </button>
        </div>
        <div class="sidebar-content">
          <div class="add-main-section">
            <button @click="showAddMainSectionModal" class="add-main-section-btn">
              <i class="mdi mdi-plus"></i>
              <span>新增大章節</span>
            </button>
          </div>
          <template v-for="(section, index) in sections" :key="section.id">
            <!-- 大標題 -->
            <div class="section-level-1">
              <div 
                :class="['section-title', { 'active': selectedSection === section.id }]"
                @click="selectSection(section.id)"
              >
                <div class="section-title-content">
                  <span>{{ getSectionNumber(index) }}. {{ section.title }}</span>
                  <div class="section-actions">
                    <button 
                      class="edit-title-btn"
                      @click.stop="showEditTitleModal(section.id, section.title, $event)"
                      title="編輯標題"
                    >
                      <i class="mdi mdi-pencil"></i>
                    </button>
                    <button 
                      class="add-subsection-btn"
                      @click.stop="showAddSubsectionModal(section.id, 1)"
                      title="新增子標題"
                    >
                      <i class="mdi mdi-plus"></i>
                    </button>
                    <button 
                      class="delete-btn"
                      @click.stop="confirmDelete(section.id, section.title)"
                      title="刪除"
                    >
                      <i class="mdi mdi-delete"></i>
                    </button>
                    <button 
                      class="toggle-btn"
                      @click.stop="toggleSection(section.id)"
                      title="展開/收合"
                    >
                      <i :class="['mdi', isExpanded(section.id) ? 'mdi-chevron-down' : 'mdi-chevron-right']"></i>
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- 子標題 -->
              <template v-if="section.children && isExpanded(section.id)">
                <div 
                  v-for="(subSection, subIndex) in section.children" 
                  :key="subSection.id"
                  class="section-level-2"
                >
                  <div 
                    :class="['section-title', { 'active': selectedSection === subSection.id }]"
                    @click="selectSection(subSection.id)"
                  >
                    <div class="section-title-content">
                      <span>{{ getAlphabetLabel(subIndex) }}. {{ subSection.title }}</span>
                      <div class="section-actions">
                        <button 
                          class="edit-title-btn"
                          @click.stop="showEditTitleModal(subSection.id, subSection.title, $event)"
                          title="編輯標題"
                        >
                          <i class="mdi mdi-pencil"></i>
                        </button>
                        <button 
                          class="add-subsection-btn"
                          @click.stop="showAddSubsectionModal(subSection.id, 2)"
                          title="新增子標題"
                        >
                          <i class="mdi mdi-plus"></i>
                        </button>
                        <button 
                          class="delete-btn"
                          @click.stop="confirmDelete(subSection.id, subSection.title)"
                          title="刪除"
                        >
                          <i class="mdi mdi-delete"></i>
                        </button>
                        <button 
                          v-if="subSection.children"
                          class="toggle-btn"
                          @click.stop="toggleSubSection(subSection.id)"
                          title="展開/收合"
                        >
                          <i :class="['mdi', isExpanded(subSection.id) ? 'mdi-chevron-down' : 'mdi-chevron-right']"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 內容項目 -->
                  <div v-if="subSection.children" :class="{ 'hidden': !isExpanded(subSection.id) }">
                    <div 
                      v-for="(item, itemIndex) in subSection.children" 
                      :key="item.id"
                      class="section-level-3"
                    >
                      <div 
                        :class="['section-title', { 'active': selectedSection === item.id }]"
                        @click.stop="selectSection(item.id)"
                      >
                        <div class="section-title-content">
                          <span>{{ getRomanNumeral(itemIndex + 1) }}. {{ item.title }}</span>
                          <div class="section-actions">
                            <button 
                              class="edit-title-btn"
                              @click.stop="showEditTitleModal(item.id, item.title, $event)"
                              title="編輯標題"
                            >
                              <i class="mdi mdi-pencil"></i>
                            </button>
                            <button 
                              class="delete-btn"
                              @click.stop="confirmDelete(item.id, item.title)"
                              title="刪除"
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
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 主要編輯區域 -->
    <div :class="['main-content', { 'expanded': isSidebarCollapsed }]">
      <div class="editor-header">
        <div class="header-content">
          <h2>{{ getCurrentSectionTitle() }}</h2>
          <div class="theme-toggle">
            <button @click="toggleTheme" class="theme-button">
              <i :class="['mdi', theme === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny']"></i>
            </button>
          </div>
        </div>
      </div>
      
      <div class="editor-content">
        <!-- 只有在選中最小層級標題時才顯示輸入框 -->
        <div v-if="isLeafSection(selectedSection)" class="input-area">
          <div class="content-wrapper">
            <textarea 
              v-model="sectionContents[selectedSection]" 
              class="content-textarea"
              :placeholder="'請輸入' + getCurrentSectionTitle() + '的內容...'"
            ></textarea>
            
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
          請選擇左側小標題以進行編輯
        </div>
      </div>
    </div>
  </div>

  <!-- 新增子標題的彈出視窗 -->
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <h3>{{ getModalTitle(currentLevel) }}</h3>
      <div class="modal-form">
        <input 
          v-model="newSubsectionTitle" 
          type="text" 
          :placeholder="getModalPlaceholder(currentLevel)"
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
      <h3>{{ getEditModalTitle(editingSectionId) }}</h3>
      <div class="modal-form">
        <input 
          v-model="editingTitle" 
          type="text" 
          :placeholder="getEditModalPlaceholder(editingSectionId)"
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
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import { useUserStore } from '@/stores/user'
import { useCompanyInfoStore } from '@/stores/companyInfo'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'
import CompanyInfoEditNav from './CompanyInfoEditNav.vue'
import { v4 as uuidv4 } from 'uuid'

// 使用 toast
const toast = useToast()

// 使用 router 和 route
const router = useRouter()
const route = useRoute()

// 使用 store
const userStore = useUserStore()
const companyInfoStore = useCompanyInfoStore()

// 從 store 中獲取狀態
const sections = computed(() => companyInfoStore.sections)
const selectedSection = computed(() => companyInfoStore.selectedSection)
const expandedSections = computed(() => companyInfoStore.expandedSections)
const sectionContents = computed(() => companyInfoStore.sectionContents)
const comments = computed(() => companyInfoStore.comments)
const showCommentPanel = computed(() => companyInfoStore.showCommentPanel)
const theme = computed(() => companyInfoStore.theme)

// 側邊欄狀態
const isSidebarCollapsed = ref(false)

// 新增子標題相關的響應式變量
const showModal = ref(false)
const newSubsectionTitle = ref('')
const currentParentId = ref(null)
const currentLevel = ref(1)

// 添加編輯標題相關的響應式變量
const showEditModal = ref(false)
const editingTitle = ref('')
const editingSectionId = ref(null)

// 新增大章節相關的響應式變量
const showMainSectionModal = ref(false)
const newMainSectionTitle = ref('')

// 初始化函数
const initializeUser = async () => {
    if (!userStore.isAuthenticated) {
        await userStore.initializeFromStorage()
        if (!userStore.isAuthenticated && route.path !== '/login' && route.path !== '/signup') {
            window.location.href = '/login'
            return
        }
    }
    await userStore.fetchUserProfile()
}

// 加載資產內容
const loadAssetContent = async (assetId) => {
  try {
    const content = await companyInfoStore.fetchAssetContent(userStore.organizationID, assetId)
    if (content && content.content) {
      companyInfoStore.assetName = content.assetName
      companyInfoStore.sections = content.content.chapters.map(chapter => ({
        id: uuidv4(),
        title: chapter.chapterTitle,
        children: chapter.subChapters.map(subChapter => ({
          id: uuidv4(),
          title: subChapter.subChapterTitle,
          children: subChapter.subSubChapters.map(subSubChapter => ({
            id: subSubChapter.BlockID,
            title: subSubChapter.subSubChapterTitle,
            blockId: subSubChapter.BlockID,
            accessPermissions: subSubChapter.access_permissions
          }))
        }))
      }))
    }
  } catch (error) {
    console.error('加載資產內容失敗:', error)
    toast.error('加載資產內容失敗：' + error.message)
  }
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
  
  await initializeUser()
  await loadAssetContent(assetId)
  initializeExpandedSections()
})

// 方法
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// 輔助函數：將數字轉換為字母標籤 (A, B, C...)
const getAlphabetLabel = (index) => {
  return String.fromCharCode(65 + index)
}

// 輔助函數：將數字轉換為羅馬數字
const getRomanNumeral = (num) => {
  const romanNumerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx']
  return romanNumerals[num - 1] || num
}

// 初始化展開狀態
const initializeExpandedSections = () => {
  sections.value.forEach(section => {
    expandedSections.value.add(section.id)
  })
}

// 使用 store 中的方法
const selectSection = async (sectionId) => {
  const section = companyInfoStore.findSectionById(sectionId)
  if (section) {
    await companyInfoStore.selectSection(sectionId)
  }
}

// 展開/收合章節
const toggleSection = companyInfoStore.toggleSection
// 是否展開
const isExpanded = (sectionId) => expandedSections.value.has(sectionId)
// 獲取當前章節標題
const getCurrentSectionTitle = companyInfoStore.getCurrentSectionTitle
// 是否為葉子節點
const isLeafSection = companyInfoStore.isLeafSection

// 主題切換
const handleThemeChange = (newTheme) => {
  companyInfoStore.theme = newTheme
}

// 字體大小切換
const handleFontSizeChange = (size) => {
  const fontSizes = {
    small: '14px',
    medium: '16px',
    large: '20px'
  }
  document.documentElement.style.setProperty('--editor-font-size', fontSizes[size])
}

// 添加檢查章節名稱是否重複的方法
const checkDuplicateTitle = (title, level, excludeId = null) => {
  const checkInArray = (sectionsArr, currentPath = []) => {
    for (const section of sectionsArr) {
      // 跳過當前正在編輯的章節
      if (section.id === excludeId) {
        continue
      }

      const path = [section, ...currentPath]
      const pathLength = path.length

      // 檢查對應層級的標題
      if ((level === 0 && pathLength === 1 && section.title === title) || // 大章節
          (level === 1 && pathLength === 2 && section.title === title) || // 中章節
          (level === 2 && pathLength === 3 && section.title === title)) { // 小章節
        return true
      }

      // 繼續檢查子章節
      if (section.children) {
        const isDuplicate = checkInArray(section.children, path)
        if (isDuplicate) return true
      }
    }
    return false
  }

  return checkInArray(sections.value)
}

// 修改新增子標題的方法
const addSubsection = () => {
  if (!newSubsectionTitle.value.trim()) {
    alert('請輸入子標題名稱')
    return
  }

  // 檢查標題是否重複
  if (checkDuplicateTitle(newSubsectionTitle.value.trim(), currentLevel.value)) {
    toast.error(currentLevel.value === 1 ? '中章節名稱重複' : '小章節名稱重複')
    return
  }

  const newId = uuidv4()
  const newSubsection = {
    id: newId,
    title: newSubsectionTitle.value.trim(),
    children: currentLevel.value === 1 ? [] : null
  }

  const updateSections = (sectionsArr) => {
    return sectionsArr.map(section => {
      if (section.id === currentParentId.value) {
        // 根據當前層級記錄日誌
        if (currentLevel.value === 1) {
          console.log("大標題名稱", section.title, "新增中標題", newSubsection.title)
          companyInfoStore.addCompanyInfoChapter(route.query.assetId, section.title, newSubsection.title, 2)
        } else if (currentLevel.value === 2) {
          console.log("中標題名稱", section.title, "新增小標題", newSubsection.title)
          companyInfoStore.addCompanyInfoChapter(route.query.assetId, section.title, newSubsection.title, 3)
        }
        return {
          ...section,
          children: [...(section.children || []), newSubsection]
        }
      }
      if (section.children) {
        return {
          ...section,
          children: updateSections(section.children)
        }
      }
      return section
    })
  }

  companyInfoStore.sections = updateSections(sections.value)
  expandedSections.value.add(currentParentId.value)
  closeModal()
}

const showAddSubsectionModal = (parentId, level) => {
  currentParentId.value = parentId
  currentLevel.value = level
  showModal.value = true
  newSubsectionTitle.value = ''
}

const closeModal = () => {
  showModal.value = false
  newSubsectionTitle.value = ''
}

// 修改新增大章節的方法
const addMainSection = () => {
  if (!newMainSectionTitle.value.trim()) {
    alert('請輸入大章節名稱')
    return
  }

  // 檢查標題是否重複
  if (checkDuplicateTitle(newMainSectionTitle.value.trim(), 0)) {
    toast.error('大章節名稱重複')
    return
  }

  const newSection = {
    id: uuidv4(),
    title: newMainSectionTitle.value.trim(),
    children: []
  }

  // console.log("新增大標題", newSection.title)
  companyInfoStore.addCompanyInfoChapter(route.query.assetId, newSection.title, newSection.title, 1)
  companyInfoStore.sections.push(newSection)
  expandedSections.value.add(newSection.id)
  closeMainSectionModal()
}

const showAddMainSectionModal = () => {
  showMainSectionModal.value = true
  newMainSectionTitle.value = ''
}

const closeMainSectionModal = () => {
  showMainSectionModal.value = false
  newMainSectionTitle.value = ''
}

// 註解相關方法
const updateCommentStatus = (sectionId, status) => {
  if (comments.value[sectionId]) {
    comments.value[sectionId].status = status
  }
}

const updateCommentContent = (sectionId, content) => {
  if (comments.value[sectionId]) {
    comments.value[sectionId] = {
      ...comments.value[sectionId],
      content
    }
  }
}

const addComment = (sectionId) => {
  if (!comments.value[sectionId]) {
    comments.value[sectionId] = {
      create_user: 1, // 這裡應該使用實際的用戶ID
      content: '',
      status: 'unfinished',
      section: getCurrentSectionTitle(), // 添加章節信息
      created_at: new Date().toISOString() // 添加創建時間
    }
  }
  showCommentPanel.value = true
}

const closeCommentPanel = () => {
  showCommentPanel.value = false
}

const toggleSubSection = (sectionId) => {
  companyInfoStore.toggleSection(sectionId)
}

// 修改更新章節標題的方法
const updateSectionTitle = () => {
  if (!editingTitle.value.trim()) {
    alert('請輸入標題名稱')
    return
  }

  const updateTitle = (sectionsArr) => {
    return sectionsArr.map(section => {
      if (section.id === editingSectionId.value) {
        // 獲取章節層級
        const result = companyInfoStore.findSectionAndPath(editingSectionId.value)
        if (result) {
          const pathLength = result.path.length
          // 檢查標題是否重複
          if (checkDuplicateTitle(editingTitle.value.trim(), pathLength, editingSectionId.value)) {
            if (pathLength === 0) {
              toast.error('大章節名稱重複')
            } else if (pathLength === 1) {
              toast.error('中章節名稱重複')
            } else if (pathLength === 2) {
              toast.error('小章節名稱重複')
            }
            return section
          }

          // 記錄日誌
          if (pathLength === 0) {
            console.log("編輯大標題", section.title, editingTitle.value.trim())
          } else if (pathLength === 1) {
            console.log("編輯中標題", section.title, editingTitle.value.trim())
          } else if (pathLength === 2) {
            console.log("編輯小標題", section.title, editingTitle.value.trim())
          }
        }
        return { ...section, title: editingTitle.value.trim() }
      }
      if (section.children) {
        return {
          ...section,
          children: updateTitle(section.children)
        }
      }
      return section
    })
  }

  const newSections = updateTitle(sections.value)
  // 只有在沒有重複標題時才更新
  if (newSections !== sections.value) {
    companyInfoStore.sections = newSections
    closeEditModal()
  }
}

const closeEditModal = () => {
  showEditModal.value = false
  editingTitle.value = ''
  editingSectionId.value = null
}

// 刪除章節相關方法
const deleteSection = async (sectionId) => {
  if (selectedSection.value === sectionId) {
    selectedSection.value = null
  }
  
  if (expandedSections.value.has(sectionId)) {
    expandedSections.value.delete(sectionId)
  }
  
  if (sectionContents.value[sectionId]) {
    delete sectionContents.value[sectionId]
  }
  if (comments.value[sectionId]) {
    delete comments.value[sectionId]
  }

  // 在刪除前獲取章節信息
  const sectionToDelete = companyInfoStore.findSectionById(sectionId)
  const pathInfo = companyInfoStore.findSectionAndPath(sectionId)

  const deleteFromArray = (arr) => {
    const newArr = [...arr]
    const index = newArr.findIndex(item => item.id === sectionId)
    if (index !== -1) {
      newArr.splice(index, 1)
      return { found: true, array: newArr }
    }
    
    for (let i = 0; i < newArr.length; i++) {
      if (newArr[i].children) {
        const result = deleteFromArray(newArr[i].children)
        if (result.found) {
          newArr[i] = { ...newArr[i], children: result.array }
          return { found: true, array: newArr }
        }
      }
    }
    return { found: false, array: newArr }
  }

  const result = deleteFromArray(sections.value)
  if (result.found && sectionToDelete && pathInfo) {
    // 根據路徑長度判斷章節層級並記錄日誌
    const pathLength = pathInfo.path.length
    if (pathLength === 0) {
      console.log("刪除大標題", sectionToDelete.title)
    } else if (pathLength === 1) {
      console.log("刪除中標題", sectionToDelete.title)
    } else if (pathLength === 2) {
      console.log("刪除小標題", sectionToDelete.title)
    }
    companyInfoStore.sections = result.array
  }
}

const confirmDelete = async (sectionId, title) => {
  if (confirm(`確定要刪除「${title}」嗎？此操作無法復原。`)) {
    await deleteSection(sectionId)
  }
}

// 生成章節序號的方法
const getSectionNumber = (index) => {
  let visibleIndex = 0
  sections.value.forEach((section, i) => {
    if (i < index) {
      visibleIndex++
    }
  })
  return visibleIndex + 1
}

const toggleTheme = () => {
  companyInfoStore.theme = companyInfoStore.theme === 'light' ? 'dark' : 'light'
}

// 格式化資料的方法
const formatDataToJson = () => {
  const result = []
  
  sections.value.forEach(section => {
    const sectionData = {}
    
    if (section.children) {
      const subSectionData = {}
      
      section.children.forEach(subSection => {
        const itemData = {}
        
        if (subSection.children) {
          subSection.children.forEach(item => {
            itemData[item.title] = {
              content: sectionContents.value[item.id] || '',
              comment: comments.value[item.id] || null
            }
          })
        }
        
        subSectionData[subSection.title] = itemData
      })
      
      sectionData[section.title] = subSectionData
    }
    
    result.push(sectionData)
  })
  
  return result
}

// 提供給子組件的儲存方法
const handleSave = () => {
  try {
    // const formattedData = formatDataToJson()
    // console.log(JSON.stringify(formattedData, null, 2))
    // selectSection(section.id)
    // toast.success('儲存成功')
    return true
  } catch (error) {
    console.error('儲存失敗:', error)
    toast.error('儲存失敗：' + error.message)
    return false
  }
}

// 提供儲存方法給子組件
provide('handleSave', handleSave)

// 在 script setup 部分添加以下方法
const getModalTitle = (level) => {
  switch (level) {
    case 1:
      return '新增中章節'
    case 2:
      return '新增小章節'
    default:
      return '新增章節'
  }
}

const getModalPlaceholder = (level) => {
  switch (level) {
    case 1:
      return '請輸入中章節名稱'
    case 2:
      return '請輸入小章節名稱'
    default:
      return '請輸入章節名稱'
  }
}

const getEditModalTitle = (sectionId) => {
  try {
    if (!sectionId) return '編輯標題'
    
    const section = companyInfoStore.findSectionById(sectionId)
    if (!section) return '編輯標題'
    
    const result = companyInfoStore.findSectionAndPath(sectionId)
    if (!result) return '編輯標題'
    
    // 根據路徑長度判斷章節層級
    const pathLength = result.path.length
    if (pathLength === 0) return '編輯大章節'  // 頂層，沒有父節點
    if (pathLength === 1) return '編輯中章節'  // 有一個父節點
    if (pathLength === 2) return '編輯小章節'  // 有兩個父節點
    return '編輯標題'
  } catch (error) {
    console.error('獲取編輯標題時出錯:', error)
    return '編輯標題'
  }
}

const getEditModalPlaceholder = (sectionId) => {
  try {
    if (!sectionId) return '請輸入標題名稱'
    
    const section = companyInfoStore.findSectionById(sectionId)
    if (!section) return '請輸入標題名稱'
    
    const result = companyInfoStore.findSectionAndPath(sectionId)
    if (!result) return '請輸入標題名稱'
    
    // 根據路徑長度判斷章節層級
    const pathLength = result.path.length
    if (pathLength === 0) return '請輸入大章節名稱'  // 頂層，沒有父節點
    if (pathLength === 1) return '請輸入中章節名稱'  // 有一個父節點
    if (pathLength === 2) return '請輸入小章節名稱'  // 有兩個父節點
    return '請輸入標題名稱'
  } catch (error) {
    console.error('獲取輸入提示時出錯:', error)
    return '請輸入標題名稱'
  }
}

const showEditTitleModal = (sectionId, title, event) => {
  if (event) {
    event.stopPropagation()
  }
  editingSectionId.value = sectionId
  editingTitle.value = title
  showEditModal.value = true
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
  width: 318px;
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
  margin-bottom: 1rem;
}

.section-level-2 {
  padding-left: 1.5rem;
  margin-top: 0.5rem;
}

.section-level-3 {
  padding-left: 1.5rem;
  margin-top: 0.25rem;
}

.section-title {
  padding: 0.5rem 1rem;
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
  padding: 2rem;
  transition: all 0.3s ease;
  margin-left: 300px;
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
  justify-content: space-between;
  align-items: center;
  width: 100%;
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
  min-height: 200px;
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
  color: #e2e8f0;
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

.add-subsection-btn i {
  font-size: 1.2rem;
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
  gap: 1rem;
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

.dark .add-main-section-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.add-main-section-btn i {
  font-size: 1.2rem;
}

/* 確保 modal 樣式與其他 modal 一致 */
.modal-overlay {
  z-index: 1001;
}

/* 摺疊/展開按鈕樣式 */
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
}

.light .toggle-btn {
  color: #4b5563;
}

.dark .toggle-btn {
  color: #e2e8f0;
}

.toggle-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>