import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCompanyStore = defineStore('company', () => {
  // 產業列表
  const industries = ref([
    {
      name: "金融業",
      templateUrl: "https://raw.githubusercontent.com/wade0426/1110932038/refs/heads/main/公司資料_資產資料_格式_金融業.json"
    },
    {
      name: "科技業",
      templateUrl: "https://raw.githubusercontent.com/wade0426/ChatESG_new/main/definition/%E5%85%AC%E5%8F%B8%E8%B3%87%E6%96%99_%E8%B3%87%E7%94%A2%E8%B3%87%E6%96%99_%E6%A0%BC%E5%BC%8F.json"
    },
    {
      name: "製造業",
      templateUrl: "https://raw.githubusercontent.com/wade0426/ChatESG_new/main/definition/%E5%85%AC%E5%8F%B8%E8%B3%87%E6%96%99_%E8%B3%87%E7%94%A2%E8%B3%87%E6%96%99_%E6%A0%BC%E5%BC%8F.json"
    },
    {
      name: "服務業",
      templateUrl: "https://raw.githubusercontent.com/wade0426/ChatESG_new/main/definition/%E5%85%AC%E5%8F%B8%E8%B3%87%E6%96%99_%E8%B3%87%E7%94%A2%E8%B3%87%E6%96%99_%E6%A0%BC%E5%BC%8F.json"
    },
    {
      name: "零售業",
      templateUrl: "https://raw.githubusercontent.com/wade0426/ChatESG_new/main/definition/%E5%85%AC%E5%8F%B8%E8%B3%87%E6%96%99_%E8%B3%87%E7%94%A2%E8%B3%87%E6%96%99_%E6%A0%BC%E5%BC%8F.json"
    }
  ])

  // 創建公司基本資料
  const createCompanyInfo = async (companyData) => {
    try {
      // 獲取選擇的產業模板
      const selectedIndustry = industries.value.find(industry => industry.name === companyData.industry)
      if (!selectedIndustry) {
        throw new Error('找不到對應的產業模板')
      }

      // 準備請求資料
      const requestData = {
        company_name: companyData.name,
        creator_id: companyData.creator,
        organization_id: companyData.organizationID,
        template_url: selectedIndustry.templateUrl
      }

      // 發送 API 請求
      const response = await fetch('http://localhost:8000/api/organizations/create_company_table', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '創建公司基本資料失敗')
      }

      const data = await response.json()
      if (data.status !== 'success') {
        throw new Error(data.message || '創建公司基本資料失敗')
      }

      return data
    } catch (error) {
      console.error('創建公司基本資料失敗:', error)
      throw error
    }
  }

  return {
    industries,
    createCompanyInfo
  }
}) 