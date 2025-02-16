<template>
  <div v-show="isVisible" class="workflow-settings-modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>設定審核流程 - {{ report?.assetName }}</h3>
        <button class="close-btn" @click="hideModal">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <!-- 載入中提示 -->
        <div v-if="loading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <p>載入中...</p>
        </div>

        <div v-else class="layout-container">
          <!-- 左側：章節列表 -->
          <div class="chapter-list">
            <h4>章節列表</h4>
            <div class="chapter-items">
              <label 
                v-for="(chapter, index) in chapters" 
                :key="index"
                class="chapter-item"
                :class="{ 'selected': selectedChapter === chapter }"
              >
                <input 
                  type="radio" 
                  :value="chapter"
                  v-model="selectedChapterId"
                  @change="handleChapterSelect(chapter)"
                >
                <span class="chapter-title">{{ chapter }}</span>
              </label>
            </div>
          </div>

          <!-- 右側：審核階段設定 -->
          <div class="approval-stages">
            <div class="stages-header">
              <div class="current-chapter">
                <span class="current-chapter-label">當前設定章節</span>
                <h4 class="current-chapter-title">{{ selectedChapter || '尚未選擇章節' }}</h4>
              </div>
              <button 
                class="add-stage-btn"
                @click="addNewStage"
                :disabled="!selectedChapter"
              >
                <i class="fas fa-plus"></i> 新增審核階段
              </button>
            </div>

            <!-- 審核階段列表 -->
            <draggable 
              v-model="stages" 
              class="stages-list"
              :disabled="!selectedChapter"
              item-key="id"
              handle=".drag-handle"
              @end="handleDragEnd"
            >
              <template #item="{ element: stage }">
                <div class="stage-card">
                  <div class="drag-handle">
                    <i class="fas fa-grip-vertical"></i>
                  </div>
                  <div class="stage-content">
                    <div class="stage-header">
                      <h5>{{ stage.name }}</h5>
                      <div class="stage-actions">
                        <button 
                          class="edit-btn" 
                          @click="() => {
                            console.log('Stage to edit:', stage);
                            editStage(stage);
                          }"
                        >
                          <i class="fas fa-edit"></i>
                        </button>
                        <button class="delete-btn" @click="confirmDeleteStage(stage)">
                          <i class="fas fa-trash"></i>
                        </button>
                      </div>
                    </div>
                    <div class="approver-groups">
                      <span 
                        v-for="group in stage.approverGroups" 
                        :key="group.roleId" 
                        class="approver-group"
                      >
                        {{ group.roleName }}
                      </span>
                    </div>
                  </div>
                </div>
              </template>
            </draggable>

            <!-- 無審核階段時的提示 -->
            <div v-if="selectedChapter && !stages.length" class="no-stages">
              <i class="fas fa-tasks empty-icon"></i>
              <p class="primary-text">這裡空空的</p>
              <p class="secondary-text">點擊右上角的「新增審核階段」開始設定審核流程吧！</p>
            </div>

            <!-- 未選擇章節時的提示 -->
            <div v-if="!selectedChapter" class="no-chapter-selected">
              <i class="fas fa-hand-point-left empty-icon"></i>
              <p class="primary-text">請選擇章節</p>
              <p class="secondary-text">在左側「章節列表」中選擇您要設定審核流程的章節</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部按鈕 -->
      <div class="modal-footer">
        <button class="secondary-btn" @click="hideModal">取消</button>
        <button 
          class="primary-btn" 
          @click="saveSettings"
          :disabled="!hasChanges || loading"
        >
          {{ loading ? '儲存中...' : '儲存設定' }}
        </button>
      </div>
    </div>

    <!-- 審核階段設定表單 -->
    <div v-if="showStageForm" class="stage-form-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingStage ? '編輯審核階段' : '新增審核階段' }}</h3>
          <button class="close-btn" @click="closeStageForm">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label for="stageName">階段名稱</label>
            <input 
              id="stageName"
              v-model="stageForm.name"
              type="text"
              placeholder="輸入階段名稱"
              :class="{ 'error': stageFormErrors.name }"
            >
            <span class="error-message" v-if="stageFormErrors.name">
              {{ stageFormErrors.name }}
            </span>
          </div>

          <div class="form-group">
            <label>審核身分組</label>
            <div class="approver-groups-select">
              <label 
                v-for="group in availableGroups" 
                :key="group.roleId"
                class="group-checkbox"
              >
                <input 
                  type="checkbox"
                  :value="group.roleId"
                  :checked="stageForm.approverGroupIds.includes(group.roleId)"
                  @change="(e) => {
                    const newApproverGroupIds = [...stageForm.approverGroupIds]
                    if (e.target.checked) {
                      if (!newApproverGroupIds.includes(group.roleId)) {
                        newApproverGroupIds.push(group.roleId)
                      }
                    } else {
                      const index = newApproverGroupIds.indexOf(group.roleId)
                      if (index > -1) {
                        newApproverGroupIds.splice(index, 1)
                      }
                    }
                    stageForm.approverGroupIds = newApproverGroupIds
                    console.log('複選框變化:', {
                      roleId: group.roleId,
                      checked: e.target.checked,
                      currentIds: newApproverGroupIds
                    })
                  }"
                >
                <span class="group-name">{{ group.roleName }}</span>
              </label>
            </div>
            <span class="error-message" v-if="stageFormErrors.approverGroups">
              {{ stageFormErrors.approverGroups }}
            </span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="secondary-btn" @click="closeStageForm">取消</button>
          <button 
            class="primary-btn" 
            @click="saveStage"
            :disabled="!isStageFormValid"
          >
            確認
          </button>
        </div>
      </div>
    </div>

    <!-- 確認刪除對話框 -->
    <div v-if="showDeleteConfirm" class="delete-confirm-modal">
      <div class="modal-content delete-confirm-content">
        <div class="delete-icon-wrapper">
          <i class="fas fa-exclamation-triangle delete-icon"></i>
        </div>
        <h3>確認移除審核階段</h3>
        <p class="delete-message">
          確定要移除審核階段「{{ stageToDelete?.name }}」嗎？<br>
          <span class="warning-text">移除後將無法恢復。</span>
        </p>
        <div class="modal-footer">
          <button class="outline-btn" @click="cancelDelete">
            <i class="fas fa-times"></i> 取消
          </button>
          <button class="delete-btn" @click="confirmDelete">
            <i class="fas fa-trash-alt"></i> 確認移除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import { useWorkflowStore } from '@/stores/workflow'
import { useUserStore } from '@/stores/user'
import draggable from 'vuedraggable'

const toast = useToast()
const workflowStore = useWorkflowStore()
const userStore = useUserStore()

// Props
const props = defineProps({
  report: {
    type: Object,
    required: false,
    default: null
  }
})

// 組件狀態
const isVisible = ref(false)
const selectedChapterId = ref(null)
const selectedChapter = ref(null)
const stages = ref([])
const originalStages = ref([])
const showStageForm = ref(false)
const editingStage = ref(null)
const showDeleteConfirm = ref(false)
const stageToDelete = ref(null)

// 從 store 獲取數據
const chapters = computed(() => workflowStore.chapters)
const availableGroups = computed(() => workflowStore.approverGroups)
const loading = computed(() => workflowStore.loading)

// 表單狀態
const stageForm = reactive({
  name: '',
  approverGroupIds: []
})

const stageFormErrors = reactive({
  name: '',
  approverGroups: ''
})

// 計算屬性
const hasChanges = computed(() => {
  if (!stages.value.length && !originalStages.value.length) return false
  return JSON.stringify(stages.value) !== JSON.stringify(originalStages.value)
})

const isStageFormValid = computed(() => {
  return stageForm.name && stageForm.approverGroupIds.length > 0
})

// 監聽選中的章節變化
watch(selectedChapterId, async (newChapter) => {
  if (newChapter) {
    try {
      selectedChapter.value = newChapter
      selectedChapterId.value = newChapter
      
      const fetchedStages = await workflowStore.fetchWorkflowSettings(props.report.assetID, newChapter)
      console.log('獲取到的階段數據:', JSON.stringify(fetchedStages, null, 2))
      
      // 使用深拷貝確保每個階段的 approverGroups 都是完全獨立的
      stages.value = fetchedStages.map(stage => ({
        id: stage.id,
        name: stage.name,
        approverGroups: stage.approverGroups.map(group => ({
          roleId: group.roleId,
          roleName: group.roleName,
          description: group.description,
          color: group.color,
          createdAt: group.createdAt
        }))
      }))
      
      // 為 originalStages 也創建一個深拷貝
      originalStages.value = JSON.parse(JSON.stringify(stages.value))
      
      console.log('設置後的階段數據:', JSON.stringify(stages.value, null, 2))
    } catch (error) {
      console.error('獲取審核流程設定失敗:', error)
      toast.error('獲取審核流程設定失敗')
    }
  }
})

// 監聽 report 的變化
watch(() => props.report, (newReport) => {
  console.log('Report changed:', newReport);
}, { deep: true });

// 方法
const showModal = async () => {
  try {
    if (!props.report?.assetID) {
      console.error('報告書資訊不完整:', props.report);
      toast.error('無法開啟審核流程設定：報告書資訊不完整')
      return
    }

    isVisible.value = true
    // 重置狀態
    selectedChapterId.value = null
    selectedChapter.value = null
    stages.value = []
    originalStages.value = []

    // 獲取章節列表和審核身分組
    await Promise.all([
      workflowStore.fetchChapters(props.report.assetID),
      workflowStore.fetchApproverGroups(userStore.organizationID)
    ])
  } catch (error) {
    console.error('初始化數據失敗:', error)
    toast.error('載入數據失敗，請稍後再試')
    isVisible.value = false
  }
}

const hideModal = () => {
  if (hasChanges.value) {
    if (confirm('您有未儲存的變更，確定要離開嗎？')) {
      closeModal()
    }
  } else {
    closeModal()
  }
}

const closeModal = () => {
  isVisible.value = false
  resetState()
}

const resetState = () => {
  selectedChapterId.value = null
  selectedChapter.value = null
  stages.value = []
  originalStages.value = []
  showStageForm.value = false
  editingStage.value = null
  showDeleteConfirm.value = false
  stageToDelete.value = null
  workflowStore.resetState()
}

const handleChapterSelect = async (chapter) => {
  selectedChapter.value = chapter
  selectedChapterId.value = chapter
  
  try {
    const fetchedStages = await workflowStore.fetchWorkflowSettings(props.report.assetID, chapter)
    console.log('獲取到的階段數據:', JSON.stringify(fetchedStages, null, 2))
    
    // 使用深拷貝確保每個階段的 approverGroups 都是完全獨立的
    stages.value = fetchedStages.map(stage => ({
      id: stage.id,
      name: stage.name,
      approverGroups: stage.approverGroups.map(group => ({
        roleId: group.roleId,
        roleName: group.roleName,
        description: group.description,
        color: group.color,
        createdAt: group.createdAt
      }))
    }))
    
    // 為 originalStages 也創建一個深拷貝
    originalStages.value = JSON.parse(JSON.stringify(stages.value))
    
    console.log('設置後的階段數據:', JSON.stringify(stages.value, null, 2))
  } catch (error) {
    console.error('獲取審核流程設定失敗:', error)
    toast.error('獲取審核流程設定失敗')
  }
}

const resetStageForm = () => {
  stageForm.name = ''
  stageForm.approverGroupIds = []
  stageFormErrors.name = ''
  stageFormErrors.approverGroups = ''
}

const editStage = (stage) => {
  console.log('開始編輯階段:', JSON.parse(JSON.stringify(stage)))
  
  // 重置表單
  resetStageForm()
  
  // 設置編輯狀態，使用深拷貝
  editingStage.value = JSON.parse(JSON.stringify(stage))
  showStageForm.value = true
  
  // 設置表單數據
  stageForm.name = stage.name
  
  // 確保 approverGroups 存在且是數組
  if (stage.approverGroups && Array.isArray(stage.approverGroups)) {
    // 檢查每個 roleId 是否在 availableGroups 中存在
    const validRoleIds = stage.approverGroups
      .map(group => group.roleId)
      .filter(roleId => availableGroups.value.some(g => g.roleId === roleId))
    
    if (validRoleIds.length !== stage.approverGroups.length) {
      console.warn('某些審核身分組不再可用:', 
        stage.approverGroups.filter(group => !validRoleIds.includes(group.roleId)))
    }
    
    console.log('設置審核身分組:', validRoleIds)
    // 創建新的數組
    stageForm.approverGroupIds = [...validRoleIds]
  } else {
    console.warn('審核身分組數據無效:', stage.approverGroups)
    stageForm.approverGroupIds = []
  }
}

const closeStageForm = () => {
  showStageForm.value = false
  editingStage.value = null
  resetStageForm()
}

const addNewStage = () => {
  showStageForm.value = true
  editingStage.value = null
  resetStageForm()
}

const validateStageForm = () => {
  let isValid = true
  stageFormErrors.name = ''
  stageFormErrors.approverGroups = ''

  if (!stageForm.name.trim()) {
    stageFormErrors.name = '請輸入階段名稱'
    isValid = false
  }

  // 嚴格檢查 approverGroupIds
  if (!Array.isArray(stageForm.approverGroupIds) || stageForm.approverGroupIds.length === 0) {
    stageFormErrors.approverGroups = '請選擇至少一個審核身分組'
    isValid = false
  }

  // 檢查所有選擇的 roleId 是否都存在於 availableGroups 中
  const invalidRoleIds = stageForm.approverGroupIds.filter(
    roleId => !availableGroups.value.some(group => group.roleId === roleId)
  )
  
  if (invalidRoleIds.length > 0) {
    console.error('發現無效的 roleId:', invalidRoleIds)
    stageFormErrors.approverGroups = '選擇的審核身分組無效'
    isValid = false
  }

  console.log('表單驗證結果:', isValid, stageForm, stageFormErrors)
  return isValid
}

const saveStage = () => {
  if (!validateStageForm()) return

  console.log('Saving stage with approverGroupIds:', [...stageForm.approverGroupIds])
  console.log('Available groups:', availableGroups.value)

  // 創建一個全新的 approverGroups 數組
  const newApproverGroups = stageForm.approverGroupIds
    .map(roleId => {
      const group = availableGroups.value.find(g => g.roleId === roleId)
      if (!group) {
        console.error('找不到對應的審核身分組:', roleId)
        return null
      }
      // 為每個組創建一個新的對象
      return {
        roleId: group.roleId,
        roleName: group.roleName,
        description: group.description,
        color: group.color,
        createdAt: group.createdAt
      }
    })
    .filter(Boolean)

  // 創建新的階段對象
  const newStage = {
    id: editingStage.value?.id || Date.now(),
    name: stageForm.name,
    approverGroups: newApproverGroups
  }

  // 如果沒有有效的審核身分組，不允許保存
  if (newStage.approverGroups.length === 0) {
    stageFormErrors.approverGroups = '請選擇有效的審核身分組'
    return
  }

  if (editingStage.value) {
    const index = stages.value.findIndex(s => s.id === editingStage.value.id)
    if (index !== -1) {
      // 使用深拷貝確保數據獨立
      stages.value = [
        ...stages.value.slice(0, index),
        JSON.parse(JSON.stringify(newStage)),
        ...stages.value.slice(index + 1)
      ]
    }
  } else {
    // 新增時也使用深拷貝
    stages.value = [...stages.value, JSON.parse(JSON.stringify(newStage))]
  }

  closeStageForm()
  toast.success(editingStage.value ? '審核階段已更新' : '審核階段已新增')
}

const confirmDeleteStage = (stage) => {
  stageToDelete.value = stage
  showDeleteConfirm.value = true
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  stageToDelete.value = null
}

const confirmDelete = () => {
  if (!stageToDelete.value) return

  stages.value = stages.value.filter(s => s.id !== stageToDelete.value.id)
  showDeleteConfirm.value = false
  stageToDelete.value = null
  toast.success('審核階段已刪除')
}

const handleDragEnd = () => {
  toast.success('審核階段順序已更新')
}

const saveSettings = async () => {
  if (!selectedChapter.value) return

  try {
    // 在儲存前創建一個深拷貝
    const stagesToSave = stages.value.map(stage => ({
      id: stage.id,
      name: stage.name,
      approverGroups: stage.approverGroups.map(group => ({
        roleId: group.roleId,
        roleName: group.roleName,
        description: group.description,
        color: group.color,
        createdAt: group.createdAt
      }))
    }))
    
    console.log('準備儲存的數據:', JSON.stringify(stagesToSave, null, 2))
    
    await workflowStore.saveWorkflowSettings(
      props.report.assetID,
      selectedChapter.value,
      stagesToSave
    )
    
    // 更新 originalStages，使用深拷貝
    originalStages.value = JSON.parse(JSON.stringify(stagesToSave))
    
    toast.success('審核流程設定已儲存')
    hideModal()
  } catch (error) {
    console.error('儲存審核流程設定失敗:', error)
    toast.error('儲存審核流程設定失敗')
  }
}

// 監聽 stageForm 的變化
watch(() => stageForm, (newValue) => {
  console.log('stageForm 變化:', newValue)
}, { deep: true })

// 暴露方法給父組件
defineExpose({
  showModal
})
</script>

<style scoped>
.workflow-settings-modal {
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

.modal-content {
  background-color: #2c2c2c;
  border-radius: 8px;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #fff;
  background-color: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.layout-container {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
  height: 100%;
}

/* 章節列表樣式 */
.chapter-list {
  background-color: #363636;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #444;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.chapter-list h4 {
  margin: 0 0 1rem 0;
  color: #fff;
  font-size: 1.1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #444;
}

.chapter-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.chapter-items::-webkit-scrollbar {
  width: 4px;
}

.chapter-items::-webkit-scrollbar-track {
  background: #2c2c2c;
  border-radius: 4px;
}

.chapter-items::-webkit-scrollbar-thumb {
  background: #666;
  border-radius: 4px;
}

.chapter-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 2px solid transparent;
  background-color: #2c2c2c;
}

.chapter-item:hover {
  background-color: rgba(37, 99, 235, 0.1);
  transform: translateX(4px);
}

.chapter-item.selected {
  background-color: rgba(37, 99, 235, 0.15);
  border-color: #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.5);
}

.chapter-item.selected::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: #2563eb;
  box-shadow: 0 0 12px rgba(37, 99, 235, 0.5);
}

.chapter-item.selected::after {
  content: '\f00c';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  right: 1rem;
  color: #2563eb;
  opacity: 0;
  transform: translateX(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chapter-item.selected:hover::after {
  opacity: 1;
  transform: translateX(0);
}

.chapter-item.selected .chapter-title {
  color: #ffffff;
  font-weight: 500;
  transform: translateX(4px);
}

.chapter-item input[type="radio"] {
  display: none;
}

.chapter-title {
  margin-left: 0.5rem;
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.95rem;
  line-height: 1.4;
}

/* 右側區域標題樣式 */
.stages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #363636;
  border-radius: 8px;
  border: 1px solid #444;
}

.stages-header .current-chapter {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stages-header .current-chapter-label {
  font-size: 0.875rem;
  color: #9ca3af;
}

.stages-header .current-chapter-title {
  font-size: 1.25rem;
  color: #fff;
  font-weight: 500;
}

/* 審核階段樣式 */
.approval-stages {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stages-header h4 {
  margin: 0;
  color: #fff;
}

.add-stage-btn {
  background-color: #2563eb;
  color: #fff;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.1);
  font-weight: 500;
}

.add-stage-btn:hover:not(:disabled) {
  background-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
}

.add-stage-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.1);
}

.add-stage-btn:disabled {
  background-color: #4b5563;
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
}

.add-stage-btn i {
  font-size: 0.875rem;
}

.stages-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-left: 40px;
  counter-reset: stage;
}

.stage-card {
  background-color: #363636;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  position: relative;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stage-card::before {
  content: counter(stage);
  counter-increment: stage;
  position: absolute;
  left: -40px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background-color: #2563eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.875rem;
  font-weight: 500;
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.3);
}

.stage-card::after {
    content: '';
    position: absolute;
    left: -1.5em; /* 使用 em 單位，根據字體大小自適應 */
    top: 50%;
    width: 2px;
    height: calc(100% + 1rem);
    background: linear-gradient(to bottom, #2563eb 50%, transparent 50%);
    background-size: 100% 8px;
}

.stage-card:last-child::after {
  display: none;
}

.stage-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.drag-handle {
  color: #888;
  cursor: move;
  padding: 0.25rem;
  display: flex;
  align-items: center;
}

.drag-handle i {
  transition: all 0.3s ease;
}

.stage-card:hover .drag-handle i {
  color: #fff;
}

.stage-content {
  flex: 1;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.stage-header h5 {
  margin: 0;
  color: #fff;
}

.stage-actions {
  display: flex;
  gap: 0.5rem;
}

.edit-btn,
.delete-btn {
  background: transparent;
  border: none;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.edit-btn {
  color: #60a5fa;
}

.edit-btn:hover {
  background-color: rgba(96, 165, 250, 0.1);
  color: #3b82f6;
  transform: scale(1.05);
}

.delete-btn {
  color: #ef4444;
}

.delete-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  transform: scale(1.05);
}

.edit-btn:active,
.delete-btn:active {
  transform: scale(0.95);
}

.approver-groups {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.approver-group {
  background-color: #4b5563;
  color: #fff;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
}

.no-stages,
.no-chapter-selected {
  text-align: center;
  padding: 3rem 2rem;
  color: #888;
  background-color: #363636;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.empty-icon {
  font-size: 3rem;
  color: #4b5563;
  margin-bottom: 1rem;
}

.primary-text {
  color: #fff;
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.secondary-text {
  color: #9ca3af;
  font-size: 1rem;
  margin: 0;
  max-width: 300px;
  line-height: 1.5;
}

.no-stages:hover,
.no-chapter-selected:hover {
  background-color: #404040;
  transform: translateY(-2px);
}

/* 表單樣式 */
.stage-form-modal,
.delete-confirm-modal {
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

.stage-form-modal .modal-content {
  width: 500px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #fff;
}

.form-group input[type="text"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #444;
  border-radius: 6px;
  background-color: #363636;
  color: #fff;
}

.form-group input[type="text"]:focus {
  outline: none;
  border-color: #2563eb;
}

.form-group input[type="text"].error {
  border-color: #ef4444;
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.approver-groups-select {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  padding: 0.5rem;
  background-color: #363636;
  border-radius: 6px;
}

.group-checkbox {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.group-checkbox:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.group-name {
  margin-left: 0.5rem;
  color: #fff;
}

/* 底部按鈕 */
.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #444;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.primary-btn,
.secondary-btn,
.delete-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.primary-btn {
  background-color: #2563eb;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.primary-btn:hover:not(:disabled) {
  background-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
}

.primary-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.1);
}

.primary-btn:disabled {
  background-color: #4b5563;
  cursor: not-allowed;
  opacity: 0.7;
}

.primary-btn:disabled:hover {
  box-shadow: none;
  transform: none;
}

.secondary-btn {
  background-color: transparent;
  color: #9ca3af;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: 2px solid #4b5563;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.secondary-btn:hover {
  border-color: #6b7280;
  color: #fff;
  background-color: rgba(75, 85, 99, 0.1);
}

.secondary-btn:active {
  transform: translateY(1px);
}

.delete-btn {
  background-color: #ef4444;
  border: none;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.delete-btn:hover {
  background-color: #ef4444;
  transform: translateY(-1px);
  color: #fff;
}

/* 拖曳時的樣式 */
.sortable-ghost {
  opacity: 0.5;
}

.sortable-drag {
  background-color: #2d3748;
}

/* Loading 樣式 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading-overlay p {
  color: #fff;
  font-size: 1.1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.delete-confirm-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
  animation: fadeIn 0.3s ease;
}

.delete-confirm-content {
  width: 400px;
  text-align: center;
  padding: 2rem;
}

.delete-icon-wrapper {
  margin-bottom: 1.5rem;
}

.delete-icon {
  font-size: 3rem;
  color: #f87171;
  animation: shake 0.5s ease;
}

.delete-message {
  color: #9ca3af;
  margin: 1rem 0 2rem;
  line-height: 1.6;
}

.warning-text {
  color: #f87171;
  font-weight: 500;
}

.outline-btn {
  background: transparent;
  border: 1px solid #4b5563;
  color: #9ca3af;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.outline-btn:hover {
  border-color: #9ca3af;
  color: #fff;
}

.delete-confirm-modal .delete-btn {
  width: auto;
  height: auto;
  background-color: #f87171;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.delete-confirm-modal .delete-btn:hover {
  background-color: #ef4444;
  transform: translateY(-1px);
  color: #fff;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes shake {
  0%, 100% { transform: rotate(0); }
  20%, 60% { transform: rotate(8deg); }
  40%, 80% { transform: rotate(-8deg); }
}
</style> 