<template>
  <div class="organization-dashboard">
    <div class="dashboard-header">
      <h1>組織詳細資訊</h1>
      <button class="edit-btn">編輯</button>
    </div>
    <div class="dashboard-content">
      <div class="info-card">
        <div class="org-info">
          <div class="org-avatar">
            <img :src="avatarUrl || 'https://via.placeholder.com/100'" alt="Organization Avatar">
          </div>
          <div class="org-details">
            <h2>{{ organizationName || '組織名稱' }}</h2>
            <p class="description">{{ organizationDescription || '組織描述' }}</p>
            <hr>
            <div class="meta-info">
              <p>組織ID：{{ organizationId || 'N/A' }}</p>
              <p>組織擁有者：{{ ownerName || 'N/A' }}</p>
              <p>組織成員數量：{{ memberCount || 'N/A' }}</p>
              <p>組織報告書數量：{{ reportCount || 'N/A' }}</p>
              <p>組織身份組數量：{{ identityGroupCount || 'N/A' }}</p>
              <p>創建時間：{{ createdAt || 'N/A' }}</p>
              <p>最後更新時間：{{ updatedAt || 'N/A' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { organizationStore } from '../stores/organization'
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'OrganizationDashboard',
  setup() {
    const store = organizationStore()
    const router = useRouter()

    onMounted(async () => {
      try {
        // 從 sessionStorage 獲取用戶ID
        const userID = sessionStorage.getItem('userID')
        if (!userID) {
          console.error('未找到用戶ID')
          router.push('/login')
          return
        }

        // 先獲取用戶的組織信息
        const orgInfo = await store.getOrganizationByUserId()
        if (!orgInfo || !orgInfo.organization_id) {
          console.error('未找到組織信息')
          router.push('/home')
          return
        }

        // 獲取組織詳細信息
        const success = await store.fetchOrganizationInfo(orgInfo.organization_id)
        if (!success) {
          console.error('獲取組織資訊失敗')
          router.push('/home')
        }
      } catch (error) {
        console.error('加載組織資訊時發生錯誤:', error)
        router.push('/home')
      }
    })

    return {
      organizationId: computed(() => store.organizationId),
      organizationName: computed(() => store.organizationName),
      organizationDescription: computed(() => store.description),
      avatarUrl: computed(() => store.avatarUrl),
      ownerName: computed(() => store.organizationOwner),
      memberCount: computed(() => store.memberCount),
      reportCount: computed(() => store.reportCount),
      identityGroupCount: computed(() => store.roleCount),
      createdAt: computed(() => store.createdAt),
      updatedAt: computed(() => store.updatedAt)
    }
  }
}
</script>

<style scoped>
.organization-dashboard {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
}

.edit-btn {
  padding: 8px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-btn:hover {
  background-color: #0056b3;
}

.info-card {
  background-color: #2c2c2c;
  /* background-color: white; */
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.org-info {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.org-avatar img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
  margin: 0 auto;
}

.org-details h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.description {
  color: #f5f0f0;
  margin: 20px 0 30px 0;
  font-size: 18px;
}

.meta-info {
  color: #888;
  font-size: 18px;
  width: 100%;
}

.meta-info p {
  margin: 20px 0;
  color: #f1eded;
}
</style>
