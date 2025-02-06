import { defineStore } from 'pinia'
import axios from 'axios'

export const useReportStore = defineStore('report_modal', {
  state: () => ({
    industries: [],
    company_info: [],
    templates: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchIndustries() {
      try {
        this.loading = true
        // 不使用API，先暫時使用固定值
        this.industries = [
          { value: 'finance', label: '金融業' },
          { value: 'technology', label: '科技業' },
          { value: 'manufacturing', label: '製造業' }
        ]
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async fetchOrganizationAssets(organizationID) {
      try {
        this.loading = true
        const response = await fetch('http://localhost:8000/api/organizations/get_organization_assets_for_modal', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            organization_id: organizationID
          })
        })
        if (response.ok) {
          const data = await response.json()
          // console.log("data", data)
          this.company_info = data.data.company_info.map(item => ({
            value: item.assetID,
            label: item.assetName,
            category: item.category,
            status: item.status,
            createdAt: item.createdAt,
            updatedAt: item.updatedAt
          }))
          this.templates = data.data.standard_template.map(item => ({
            value: item.assetID,
            label: item.assetName,
            category: item.category,
            status: item.status,
            createdAt: item.createdAt,
            updatedAt: item.updatedAt
          }))
        }
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    }
  }
}) 