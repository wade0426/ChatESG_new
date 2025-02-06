import { defineStore } from 'pinia'
import axios from 'axios'

export const useReportStore = defineStore('report', {
  state: () => ({
    industries: [],
    assetSizes: [
      { value: 'small', label: '小型企業' },
      { value: 'medium', label: '中型企業' },
      { value: 'large', label: '大型企業' }
    ],
    templates: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchIndustries() {
      try {
        this.loading = true
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

    async fetchTemplates() {
      try {
        this.loading = true
        const response = await axios.get('/api/templates')
        this.templates = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    }
  }
}) 