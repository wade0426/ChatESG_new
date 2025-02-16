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
        console.log("待審核列表資料：", data)
        pendingReviews.value = data.data
    } catch (error) {
      console.error('獲取待審核列表失敗:', error)
      throw error
    }
  }

  // 獲取審核資料內容
  const fetchReviewData = async (workflowInstanceID) => {
    try {
        const response = await fetch('http://localhost:8000/api/report/get_submitted_data', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            workflowInstanceID: workflowInstanceID
          })
        });

        const result = await response.json();
        
        if (result.status === 'success') {
            // 直接解析 submittedContent
            if (result.data && result.data.submittedContent) {
                try {
                    const parsedContent = JSON.parse(result.data.submittedContent);
                    currentReview.value = {
                        ...result.data,
                        ...parsedContent
                    };
                    console.log("處理後的數據:", currentReview.value);
                } catch (error) {
                    console.error('解析 submittedContent 失敗:', error);
                    currentReview.value = result.data;
                }
            } else {
                currentReview.value = result.data;
            }
            return result.data;
        } else {
            throw new Error(result.message || '獲取審核資料失敗');
        }
    } catch (error) {
      console.error('獲取審核資料內容失敗:', error);
      throw error;
    }
  }

  // 提交審核結果
  const submitReview = async (WorkflowInstanceID, userID, status, comment) => {
    try {
      // console.log("WorkflowInstanceID", WorkflowInstanceID)
      // console.log("userID", userID)
      // console.log("status", status)
      // console.log("comment", comment)
      // console.log("blockVersionID", currentReview.value.blockVersionID)
      const response = await fetch('http://localhost:8000/api/report/submit_review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          WorkflowInstanceID: WorkflowInstanceID,
          ReviewerID: userID,
          ReviewAction: status,
          ReviewComment: comment,
          BlockVersionID: currentReview.value.blockVersionID
        })
      });
      const result = await response.json();
      console.log("result", result)
      // 更新本地狀態
      // await fetchPendingReviews()
      return true
    } catch (error) {
      console.error('提交審核結果失敗:', error)
      throw error
    }
  }

  // 獲取審核歷程
  const fetchReviewHistory = async (workflowInstanceID) => {
    try {
      const response = await fetch('http://localhost:8000/api/report/get_review_progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          workflowInstanceID: workflowInstanceID,
        })
      });
      const result = await response.json();
      console.log("result", result)
      if (result.status_code === 200) {
        return result.content.data
      
      }
      // 更新本地狀態
      // await fetchPendingReviews()
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
    fetchReviewData,
    submitReview,
    fetchReviewHistory
  }
}) 