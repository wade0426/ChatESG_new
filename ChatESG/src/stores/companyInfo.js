import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useUserStore } from './user'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

export const useCompanyInfoStore = defineStore('companyInfo', () => {
  // 使用 user store
  const userStore = useUserStore()
  const route = useRoute()
  const toast = useToast()

  // 狀態
  const sections = ref([])
  const selectedSection = ref(null)
  const expandedSections = ref(new Set())
  const sectionContents = ref({})
  const comments = ref({})
  const showCommentPanel = ref(false)
  const theme = ref('dark')
  const previousSection = ref(null)
  const assetName = ref('')

  // Getters
  const getCurrentSectionTitle = () => {
    if (!selectedSection.value) return ''
    const section = findSectionById(selectedSection.value)
    if (!section) return ''
    return isLeafSection(selectedSection.value) ? section.title : ''
  }

  const isLeafSection = (sectionId) => {
    if (!sectionId) return false
    const result = findSectionAndPath(sectionId)
    if (!result) return false
    const { section, path } = result
    if (path.length !== 2) return false
    const parentSection = path[1]
    if (!parentSection.children || parentSection.children.length === 0) return false
    const grandParentSection = path[0]
    if (!grandParentSection.children || grandParentSection.children.length === 0) return false
    return !section.children || section.children.length === 0
  }

  // Actions
  const findSectionById = (id) => {
    const findInArray = (sectionsArray) => {
      for (const section of sectionsArray) {
        if (section.id === id) return section
        if (section.children) {
          const found = findInArray(section.children)
          if (found) return found
        }
      }
      return null
    }
    return findInArray(sections.value)
  }

  // 重新實現 findSectionAndPath 方法
  const findSectionAndPath = (targetId) => {
    const findInArray = (array, currentPath = []) => {
      for (const section of array) {
        // 當前路徑
        const path = [section, ...currentPath]
        
        // 如果找到目標
        if (section.id === targetId) {
          return { section, path: currentPath }
        }
        
        // 如果有子節點，繼續搜索
        if (section.children) {
          const result = findInArray(section.children, path)
          if (result) {
            return result
          }
        }
      }
      return null
    }
    
    return findInArray(sections.value)
  }

  // 切換指定章節的展開狀態
  const toggleSection = (sectionId) => {
    const newExpandedSections = new Set(expandedSections.value)
    if (newExpandedSections.has(sectionId)) {
      newExpandedSections.delete(sectionId)
      const section = findSectionById(sectionId)
      if (section && section.children) {
        section.children.forEach(child => newExpandedSections.delete(child.id))
      }
    } else {
      newExpandedSections.add(sectionId)
    }
    expandedSections.value = newExpandedSections
    selectSection(sectionId)
  }

  // 選擇章節
  const selectSection = async (sectionId) => {
    if (previousSection.value && previousSection.value !== sectionId) {
      const prevSectionInfo = findSectionById(previousSection.value)
      if (prevSectionInfo && sectionContents.value[previousSection.value]) {
        try {
          await updateSectionContent(
            prevSectionInfo.blockId,
            sectionContents.value[previousSection.value]
          )
        } catch (error) {
          console.error('更新區塊內容時發生錯誤:', error)
        }
      }
    }

    previousSection.value = sectionId
    selectedSection.value = sectionId

    const sectionInfo = findSectionById(sectionId)
    if (sectionInfo?.blockId) {
      try {
        const content = await fetchSectionContent(sectionInfo.blockId, sectionInfo.accessPermissions)
        sectionContents.value[sectionId] = content
      } catch (error) {
        console.error('獲取章節內容錯誤:', error)
        toast.error(error.message)
      }
    }
  }

  const updateSectionContent = async (blockId, content) => {
    try {
      const response = await fetch('http://localhost:8000/api/organizations/update_company_table_block', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          block_id: blockId,
          content: content,
          user_id: userStore.userID,
          asset_id: route.query.assetId
        })
      })
      
      if (!response.ok) {
        throw new Error('更新區塊內容失敗')
      }
      
      return await response.json()
    } catch (error) {
      throw error
    }
  }

  const fetchSectionContent = async (blockId, permissionChapterId) => {
    try {
      // 從 userStore 獲取用戶 ID 和角色 ID
      const userId = userStore.userID
      const roleIds = userStore.organizationRoles.map(role => role.roleID).join(',')
      const assetId = route.query.assetId
      
      if (!userId || !roleIds || !assetId) {
        throw new Error('缺少必要的用戶信息')
      }
      
      const response = await fetch('http://localhost:8000/api/organizations/get_company_table_blocks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          blockID: blockId,
          asset_id: assetId,
          user_id: userId,
          roleID: roleIds,
          permissionChapter_id: permissionChapterId
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '獲取章節內容失敗')
      }
      
      const data = await response.json()
      return data.data.content.content.text || ''
    } catch (error) {
      throw error
    }
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 新增 fetchAssetContent 方法
  const fetchAssetContent = async (organizationId, assetId) => {
    try {
      const response = await fetch('http://localhost:8000/api/organizations/get_asset_content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          organization_id: organizationId,
          asset_id: assetId
        })
      })

      if (!response.ok) {
        throw new Error('獲取資產內容失敗')
      }

      const data = await response.json()
      if (data.status === 'success') {
        return data.data
      } else {
        throw new Error(data.message || '獲取資產內容失敗')
      }
    } catch (error) {
      throw error
    }
  }

  // 新增_公司資料章節
  const addCompanyInfoChapter = async (assetId, chapterTitle, subchapterTitle, chapterLevel) => {
    try {
      const response = await fetch('http://localhost:8000/api/report/add_company_info_chapter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          asset_id: assetId,
          chapter_title: chapterTitle,
          subchapter_title: subchapterTitle,
          chapter_level: chapterLevel,
          user_id: userStore.userID
        })
      })

      if (!response.ok) {
        throw new Error('新增公司資料章節失敗')
      }

      const data = await response.json()
      if (data.status === 'success') {
        return data.data
      } else {
        throw new Error(data.message || '新增公司資料章節失敗')
      }
    } catch (error) {
      throw error
    }
  }

  // 刪除_公司資料章節
  const deleteCompanyInfoChapter = async (assetId, chapterTitle, subchapterTitle, chapterLevel) => {
    try {
      const response = await fetch('http://localhost:8000/api/report/delete_company_info_chapter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          asset_id: assetId,
          chapter_title: chapterTitle,
          subchapter_title: subchapterTitle,
          chapter_level: chapterLevel
        })
      })

      if (!response.ok) {
        throw new Error('刪除公司資料章節失敗')
      }

      const data = await response.json()
      if (data.status === 'success') {
        return data.data
      } else {
        throw new Error(data.message || '刪除公司資料章節失敗')
      }
    } catch (error) {
      throw error
    }
  }

  // 編輯_公司資料章節
  const editCompanyInfoChapter = async (assetId, chapterTitle, subchapterTitle, newChapterTitle, chapterLevel) => {
    try {
      const response = await fetch('http://localhost:8000/api/report/edit_company_info_chapter_title', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          asset_id: assetId,
          chapter_title: chapterTitle,
          subchapter_title: subchapterTitle,
          new_chapter_title: newChapterTitle,
          chapter_level: chapterLevel
        })
      })

      if (!response.ok) {
        throw new Error('編輯公司資料章節失敗')
      }

      const data = await response.json()
      if (data.status === 'success') {
        return data.data
      } else {
        throw new Error(data.message || '編輯公司資料章節失敗')
      }
    } catch (error) {
      throw error
    }
  }

  return {
    // 狀態
    sections,
    selectedSection,
    expandedSections,
    sectionContents,
    comments,
    showCommentPanel,
    theme,
    previousSection,
    assetName,

    // Getters
    getCurrentSectionTitle,
    isLeafSection,

    // Actions
    findSectionById,
    findSectionAndPath,
    toggleSection,
    selectSection,
    toggleTheme,
    fetchAssetContent,
    updateSectionContent,
    fetchSectionContent,
    addCompanyInfoChapter,
    deleteCompanyInfoChapter,
    editCompanyInfoChapter
  }
}) 