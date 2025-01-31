<template>
  <div class="membership-application-review">
    <Toasts ref="toasts" />
    <div class="page-header">
      <h1>人員申請審核 ({{ applications.length }})</h1>
    </div>
    <div class="application-list">
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> 載入中...
      </div>
      <div v-else-if="error" class="error-state">
        <i class="fas fa-exclamation-circle"></i> {{ error }}
      </div>
      <table v-else class="application-table">
        <thead>
          <tr>
            <th>申請人</th>
            <th>電子郵件</th>
            <th>申請訊息</th>
            <th>申請時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="application in applications" :key="application.id">
            <td class="name-cell">
              <span style="width: auto;"></span>
              <img v-if="application.avatarUrl" :src="application.avatarUrl" class="avatar" :alt="application.name">
              <div v-else class="avatar" :style="{ backgroundColor: getAvatarColor(application.name) }">
                {{ application.name.charAt(0).toUpperCase() }}
              </div>
              <span>{{ application.name }}</span>
            </td>
            <td>{{ application.email }}</td>
            <td>{{ application.applicationMessage || '無' }}</td>
            <td>{{ formatDate(application.applicationDate) }}</td>
            <td class="action-cell">
              <button class="approve-btn" @click="approveApplication(application)" title="允許加入">
                <i class="fas fa-check"></i>
              </button>
              <button class="reject-btn" @click="rejectApplication(application)" title="不允許加入">
                <i class="fas fa-times"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { organizationStore } from '../stores/organization'
import { useUserStore } from '../stores/user'
import Toasts from './Toasts.vue'

export default {
  name: 'MembershipApplicationReview',
  components: {
    Toasts
  },
  data() {
    return {
      applications: [],
      loading: true,
      error: null
    }
  },
  async created() {
    const store = organizationStore()
    
    // 如果 store 中沒有 organizationId，先等待初始化
    if (!store.organizationId) {
      try {
        await store.initializeOrganization()
      } catch (error) {
        console.error('初始化組織失敗:', error)
        this.error = '載入組織資訊失敗，請重新登入'
        this.loading = false
        return
      }
    }
    
    // 確保有 organizationId 後再獲取申請列表
    if (store.organizationId) {
      await this.fetchApplications()
    } else {
      this.error = '無法獲取組織資訊，請確認您已登入並屬於某個組織'
      this.loading = false
    }
  },
  methods: {
    async fetchApplications() {
      try {
        this.loading = true
        this.error = null
        const store = organizationStore()
        
        if (!store.organizationId) {
          throw new Error('未找到組織ID')
        }
        
        const response = await axios.post('http://localhost:8000/api/organizations/get_applications', {
          organization_id: store.organizationId
        })

        if (response.data.status === 'success') {
          this.applications = response.data.data
        } else {
          throw new Error('獲取申請列表失敗')
        }
      } catch (error) {
        console.error('獲取申請列表錯誤:', error)
        this.error = error.message === '未找到組織ID' 
          ? '請確認您已登入並屬於某個組織'
          : '獲取申請列表失敗，請稍後再試'
      } finally {
        this.loading = false
      }
    },
    getAvatarColor(name) {
      // 根據名字生成固定的顏色
      let hash = 0
      for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash)
      }
      const hue = Math.abs(hash % 360)
      return `hsl(${hue}, 70%, 50%)`
    },
    formatDate(dateString) {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    async approveApplication(application) {
      try {
        const userStore = useUserStore()
        const userId = userStore.userID
        
        if (!userId) {
          throw new Error('未找到用戶ID，請重新登入')
        }

        // console.log('Debug - Response:', application.id) // 18
        
        const response = await axios.post('http://localhost:8000/api/organizations/check_join', {
          application_id: application.id,
          reviewer_id: userId,
          status: 'approved'
        })

        if (response.data.status === 'success') {
          this.$refs.toasts.show(`已成功允許 ${application.name} 加入組織`, 'success')
          // 從列表中移除該申請
          this.applications = this.applications.filter(app => app.id !== application.id)
          // 重新獲取申請列表以確保數據同步
          await this.fetchApplications()
        } else {
          throw new Error('審核失敗')
        }
      } catch (error) {
        console.error('審核失敗:', error)
        let errorMessage = '審核失敗，請稍後再試'
        
        if (error.message === '未找到用戶ID，請重新登入') {
          errorMessage = error.message
        } else if (error.response?.data?.detail) {
          const detail = error.response.data.detail
          if (detail.includes('Duplicate entry')) {
            errorMessage = '該用戶可能已經是組織成員，請刷新頁面重試'
          } else if (detail.includes('該用戶已經屬於其他組織')) {
            errorMessage = '該用戶已經屬於其他組織'
          } else {
            errorMessage = detail
          }
        }
        
        this.$refs.toasts.show(errorMessage, 'error')
        // 如果是重複數據的錯誤，重新獲取申請列表
        if (errorMessage.includes('已經是組織成員')) {
          await this.fetchApplications()
        }
      }
    },
    async rejectApplication(application) {
      try {
        const userStore = useUserStore()
        const userId = userStore.userID
        
        if (!userId) {
          throw new Error('未找到用戶ID，請重新登入')
        }
        
        const response = await axios.post('http://localhost:8000/api/organizations/check_join', {
          application_id: application.id,
          reviewer_id: userId,
          status: 'rejected'
        })

        if (response.data.status === 'success') {
          this.$refs.toasts.show(`已拒絕 ${application.name} 的加入申請`, 'warning')
          // 從列表中移除該申請
          this.applications = this.applications.filter(app => app.id !== application.id)
          // 重新獲取申請列表以確保數據同步
          await this.fetchApplications()
        } else {
          throw new Error('審核失敗')
        }
      } catch (error) {
        console.error('審核失敗:', error)
        if (error.message === '未找到用戶ID，請重新登入') {
          this.$refs.toasts.show(error.message, 'error')
        } else {
          this.$refs.toasts.show(error.response?.data?.detail || '審核失敗，請稍後再試', 'error')
        }
      }
    }
  }
}
</script>

<style scoped>
.membership-application-review {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #ffffff;
}

.application-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  overflow-x: auto;
}

.application-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  color: #ffffff;
}

.application-table tr {
  border-bottom: 1px solid #444;
}

.application-table th,
.application-table td {
  text-align: center;
  vertical-align: middle;
  height: 60px;
  padding: 0;
}

.application-table th {
  color: #888;
  font-weight: 500;
  white-space: nowrap;
}

/* 設置列寬和對齊 */
.application-table th:first-child,
.application-table td:first-child {
  width: auto;
  padding: 0;
  text-align: center;
}

.application-table th:last-child,
.application-table td:last-child {
  width: 120px;
  padding: 0;
}

/* 中間列自適應 */
.application-table th:not(:first-child):not(:last-child),
.application-table td:not(:first-child):not(:last-child) {
  padding: 0 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.name-cell {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  height: 100%;
  padding: 0 16px;
  box-sizing: border-box;
  white-space: nowrap;
}

.avatar {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 18px;
  background-color: var(--avatar-color, #666);
}

.name-cell span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

.action-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 100%;
}

.approve-btn, .reject-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  font-size: 16px;
}

.approve-btn {
  background-color: #27ae60;
  color: white;
}

.reject-btn {
  background-color: #e74c3c;
  color: white;
}

.approve-btn:hover {
  background-color: #219a52;
  transform: scale(1.05);
}

.reject-btn:hover {
  background-color: #c0392b;
  transform: scale(1.05);
}

/* 響應式設計 */
@media screen and (max-width: 768px) {
  .application-table {
    font-size: 14px;
  }

  .application-table th:first-child,
  .application-table td:first-child {
    min-width: 140px;
    max-width: 200px;
  }

  .application-table th:last-child,
  .application-table td:last-child {
    width: 100px;
  }

  .name-cell {
    padding: 0 8px;
    gap: 6px;
  }
}
</style> 