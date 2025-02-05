import { defineStore } from 'pinia'
import axios from 'axios'

export const useCompanyInfoStore = defineStore('companyInfo', {
  state: () => ({
    assetContent: null,
    loading: false,
    error: null,
    isLocked: false,
    lockedBy: null,
    currentEditingSection: null
  }),

  actions: {
    async fetchAssetContent(organizationId, assetId) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.post('http://localhost:8000/api/organizations/get_asset_content', {
          organization_id: organizationId,
          asset_id: assetId
        })

        if (response.data.status === 'success') {
          this.assetContent = response.data.data
          return response.data.data
        } else {
          throw new Error('獲取資產內容失敗')
        }
      } catch (error) {
        this.error = error.message || '獲取資產內容時發生錯誤'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 