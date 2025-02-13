import { defineStore } from 'pinia'
import axios from 'axios'
import { useToast } from 'vue-toastification'

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    loading: false,
    chapters: [],
    approverGroups: [],
    workflowSettings: {}, // 格式: { chapterId: { stages: [...] } }
    workflowDetails: {}, // 格式: { chapterId: { chapterName: string, stages: [{ name: string, order: number, approverGroups: [{ roleId: string, roleName: string }] }] } }
  }),

  getters: {
    getChapterWorkflow: (state) => (chapterId) => {
      return state.workflowSettings[chapterId]?.stages || []
    },
    
    getWorkflowDetails: (state) => (chapterId) => {
      return state.workflowDetails[chapterId] || null
    },

    getAllWorkflowDetails: (state) => {
      return state.workflowDetails
    }
  },

  actions: {
    // 獲取報告書章節列表
    async fetchChapters(reportId) {
      try {
        this.loading = true
        // TODO: 替換為實際的 API 調用
        const response = await axios.post(`http://localhost:8000/api/report/get_report_chapters`, {
          AssetID: reportId
        })
        
        if (response.data.status === 'success') {
          this.chapters = response.data.data
        } else {
          throw new Error(response.data.message || '獲取章節列表失敗')
        }
      } catch (error) {
        const toast = useToast()
        toast.error(error.message || '獲取章節列表失敗')
        throw error
      } finally {
        this.loading = false
      }
    },

    // 獲取可用的身分組
    async fetchApproverGroups(organizationId) {
      try {
        this.loading = true
        // TODO: 替換為實際的 API 調用
        const response = await axios.post(`http://localhost:8000/api/organization/approver-groups`, {
          organizationID: organizationId
        })
        
        if (response.data.status === 'success') {
          this.approverGroups = response.data.data
        } else {
          throw new Error(response.data.message || '獲取審核身分組失敗')
        }
      } catch (error) {
        const toast = useToast()
        toast.error(error.message || '獲取審核身分組失敗')
        throw error
      } finally {
        this.loading = false
      }
    },

    // 獲取章節的審核流程設定
    async fetchWorkflowSettings(reportId, chapterId) {
      try {
        this.loading = true
        const response = await axios.post(`http://localhost:8000/api/report/get_workflow_stage`, {
          assetID: reportId,
          chapterName: chapterId
        })
        
        if (response.data.status === 'success') {
          // 使用深拷貝確保每個階段的 approverGroups 是獨立的
          const stages = response.data.data.map(stage => ({
            ...stage,
            approverGroups: stage.approverGroups.map(group => ({
              roleId: group.roleId,
              roleName: group.roleName,
              description: group.description,
              color: group.color,
              createdAt: group.createdAt
            }))
          }))
          
          // 更新 workflowSettings
          this.workflowSettings = {
            ...this.workflowSettings,
            [chapterId]: { 
              stages: JSON.parse(JSON.stringify(stages))
            }
          }

          // 同時更新 workflowDetails
          const chapter = this.chapters.find(c => c === chapterId)
          if (chapter) {
            this.updateWorkflowDetails(chapterId, chapter, stages)
          }

          return stages
        } else {
          throw new Error(response.data.message || '獲取審核流程設定失敗')
        }
      } catch (error) {
        const toast = useToast()
        toast.error(error.message || '獲取審核流程設定失敗')
        throw error
      } finally {
        this.loading = false
      }
    },

    // 更新工作流程詳細信息
    updateWorkflowDetails(chapterId, chapterName, stages) {
      // 使用深拷貝確保數據獨立
      const formattedStages = stages.map((stage, index) => ({
        name: stage.name,
        order: index + 1,
        approverGroups: stage.approverGroups.map(group => ({
          roleId: group.roleId,
          roleName: group.roleName
        }))
      }))

      this.workflowDetails = {
        ...this.workflowDetails,
        [chapterId]: {
          chapterName,
          stages: formattedStages
        }
      }
    },

    // 保存章節的審核流程設定
    async saveWorkflowSettings(reportId, chapterId, stages) {
      try {
        this.loading = true
        console.log('準備儲存的審核流程設定:', {
          reportId,
          chapterId,
          stages: JSON.parse(JSON.stringify(stages))
        })

        // 確保每個階段的 approverGroups 是獨立的
        const formattedStages = stages.map((stage, index) => ({
          ...stage,
          order: index + 1,
          approverGroups: stage.approverGroups.map(group => ({
            roleId: group.roleId,
            roleName: group.roleName,
            description: group.description,
            color: group.color,
            createdAt: group.createdAt
          }))
        }))

        const response = await axios.post(`http://localhost:8000/api/report/save_workflow_stage`, {
          assetID: reportId,
          chapterName: chapterId,
          stageSettings: formattedStages
        })
        
        if (response.data.status === 'success') {
          // 更新本地狀態時也使用深拷貝
          this.workflowSettings = {
            ...this.workflowSettings,
            [chapterId]: { 
              stages: JSON.parse(JSON.stringify(formattedStages))
            }
          }

          // 更新工作流程詳細信息
          const chapter = this.chapters.find(c => c === chapterId)
          if (chapter) {
            this.updateWorkflowDetails(chapterId, chapter, formattedStages)
          }
        } else {
          throw new Error(response.data.message || '儲存審核流程設定失敗')
        }
      } catch (error) {
        const toast = useToast()
        toast.error(error.message || '儲存審核流程設定失敗')
        throw error
      } finally {
        this.loading = false
      }
    },

    // 重置狀態
    resetState() {
      this.loading = false
      this.chapters = []
      this.approverGroups = []
      this.workflowSettings = {}
      this.workflowDetails = {}
    }
  }
}) 