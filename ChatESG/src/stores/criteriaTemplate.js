import { defineStore } from 'pinia'
import { useToast } from 'vue-toastification'

export const useCriteriaTemplateStore = defineStore('criteriaTemplate', {
  state: () => ({
    BlockID: '',
    AssetID: '',
    UserID: '',
    PermissionChapterID: '',
    OrganizationID: '',
    role_ids: [],
    selectedCriteria: [],
    fileName: '未命名文件',
    isLoading: false,
    lastModified: null,
    modifiedBy: null,
    isLocked: false,
    lockedBy: null,
    lockedAt: null,
    blockStatus: null
  }),

  actions: {
    // 設置 BlockID
    setBlockID(id) {
      this.BlockID = id
    },

    // 設置 UserID
    setUserID(id) {
      this.UserID = id
    },

    // 設置 AssetID
    setAssetID(id) {
      this.AssetID = id
    },

    // 設置 OrganizationID
    setOrganizationID(id) {
      this.OrganizationID = id
    },

    // 設置 role_ids
    setRoleIDs(ids) {
      this.role_ids = ids
    },

    // 設置文件名
    setFileName(name) {
      this.fileName = name
    },

    // 設置選中的準則
    setSelectedCriteria(criteria) {
      this.selectedCriteria = criteria
    },

    // 添加單個準則
    addCriterion(criterion) {
      this.selectedCriteria.push(criterion)
    },

    // 移除單個準則
    removeCriterion(gri_id) {
      this.selectedCriteria = this.selectedCriteria.filter(item => item.gri_id !== gri_id)
    },

    // 清空所有選中的準則
    clearSelectedCriteria() {
      this.selectedCriteria = []
    },

    // 檢查某個準則是否已被選中
    isCriterionSelected(gri_id) {
      return this.selectedCriteria.some(item => item.gri_id === gri_id)
    },

    // 從 API 獲取準則模板
    async fetchCriteriaTemplate() {
      const toast = useToast()
      try {
        this.isLoading = true

        // 檢查必要參數
        if (!this.AssetID || !this.OrganizationID || !this.role_ids.length) {
          throw new Error('缺少必要參數')
        }

        const response = await fetch('http://localhost:8000/api/organizations/get_standard_template', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            asset_id: this.AssetID,
            organization_id: this.OrganizationID,
            role_ids: this.role_ids
          })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || '獲取準則模板失敗')
        }

        const data = await response.json()

        if (data.status === 'success') {
          // 更新模板名稱
          this.fileName = data.data.assetName

          // 更新選中的準則
          if (data.data.content && data.data.content.selectedCriteria) {
            this.selectedCriteria = data.data.content.selectedCriteria
          }

          // 更新其他狀態
          this.lastModified = data.data.lastModified
          this.modifiedBy = data.data.modifiedBy
          this.isLocked = data.data.isLocked
          this.lockedBy = data.data.lockedBy
          this.lockedAt = data.data.lockedAt
          this.blockStatus = data.data.blockStatus
          this.BlockID = data.data.block_id
          this.PermissionChapterID = data.data.PermissionChapterID

          return data.data
        } else {
          throw new Error('獲取準則模板失敗')
        }
      } catch (error) {
        toast.error(error.message, {
          timeout: 5000,
          position: "top-right",
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true
        })
        throw error
      } finally {
        this.isLoading = false
      }
    },

    // 儲存準則模板
    async saveCriteriaTemplate() {
        const toast = useToast()
        try {
            // 準備請求數據
            const requestData = {
                asset_id: this.AssetID,
                organization_id: this.OrganizationID,
                asset_name: this.fileName,
                block_id: this.BlockID,
                permission_chapter_id: this.PermissionChapterID,
                role_ids: this.role_ids,
                selected_criteria: this.selectedCriteria,
                user_id: this.UserID
            }

            console.log(requestData)

            // 發送請求到後端 API
            const response = await fetch('http://localhost:8000/api/organizations/save_standard_template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })

            const result = await response.json()

            // 檢查回應狀態
            if (!response.ok) {
                throw new Error(result.detail || '保存失敗')
            }

            // 更新最後修改時間
            if (result.data && result.data.last_modified) {
                this.lastModified = result.data.last_modified
            }

            // 顯示成功消息
            toast.success('準則模板保存成功', {
                timeout: 5000,
                position: "top-right",
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true
            })
            return result

        } catch (error) {
            // 顯示錯誤消息
            toast.error(error.message || '保存準則模板時發生錯誤', {
                timeout: 5000,
                position: "top-right",
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true
            })
            throw error
        }
    }
  },

  getters: {
    // 獲取選中的準則數量
    selectedCount: (state) => state.selectedCriteria.length,

    // 獲取按領域分組的準則
    criteriaByDomain: (state) => {
      const grouped = {}
      state.selectedCriteria.forEach(criterion => {
        if (!grouped[criterion.domain]) {
          grouped[criterion.domain] = []
        }
        grouped[criterion.domain].push(criterion)
      })
      return grouped
    }
  }
}) 