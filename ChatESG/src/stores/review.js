import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useReviewStore = defineStore('review', () => {
  // 待審核列表
  const pendingReviews = ref([])
  
  // 當前審核的內容
  const currentReview = ref(null)
  
  // 審核歷程
  const reviewHistory = ref([])
  
  // 審核狀態列表
  const reviewStatus = {
    DRAFT: { label: '草稿', color: '#999999' },
    REVIEWING: { label: '審查中', color: '#FFA500' },
    APPROVED: { label: '已通過', color: '#008000' },
    REJECTED: { label: '已退回', color: '#FF0000' }
  }

  // 計算屬性：根據狀態過濾的待審核列表
  const filteredPendingReviews = computed(() => {
    return pendingReviews.value
  })

  // 獲取待審核列表
  const fetchPendingReviews = async (userID) => {
    try {
        const response = await fetch('http://localhost:8000/api/report/get_pending_reviews', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userID: userID
            })
        })

        const data = await response.json()
        console.log("response data", data)
        pendingReviews.value = data.data
    } catch (error) {
      console.error('獲取待審核列表失敗:', error)
      throw error
    }
  }

  // 獲取審核歷程
  const fetchReviewHistory = async (blockId) => {
    try {
      // TODO: 調用 API 獲取審核歷程
      // const response = await api.getReviewHistory(blockId)
      // reviewHistory.value = response.data
    } catch (error) {
      console.error('獲取審核歷程失敗:', error)
      throw error
    }
  }

  // 提交審核結果
  const submitReview = async (blockId, status, comment) => {
    try {
      // TODO: 調用 API 提交審核結果
      // const response = await api.submitReview({ blockId, status, comment })
      // 更新本地狀態
      await fetchPendingReviews()
      return true
    } catch (error) {
      console.error('提交審核結果失敗:', error)
      throw error
    }
  }

  return {
    pendingReviews,
    currentReview,
    reviewHistory,
    reviewStatus,
    filteredPendingReviews,
    fetchPendingReviews,
    fetchReviewHistory,
    submitReview
  }
}) 