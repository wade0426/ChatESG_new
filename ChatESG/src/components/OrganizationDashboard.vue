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
            <div class="meta-info">
              <p>組織ID：{{ organizationId || 'N/A' }}</p>
              <p>組織擁有者：{{ ownerName || 'N/A' }}</p>
              <p>組織成員數量：{{ memberCount || 'N/A' }}</p>
              <p>組織報告書數量：{{ reportCount || 'N/A' }}</p>
              <p>組織身份組數量：{{ identityGroupCount || 'N/A' }}</p>
              <p>創建時間：{{ createdAt || 'N/A' }}</p>
              <p>最後更新：{{ updatedAt || 'N/A' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OrganizationDashboard', // 組件名稱,用於在Vue開發工具中識別組件
  data() {
    return {
      // 組織基本資料
      organizationId: '', // 組織的唯一識別ID
      organizationName: '', // 組織名稱
      organizationDescription: '', // 組織描述文字
      avatarUrl: '', // 組織頭像圖片的URL
      
      // 時間相關資訊
      updatedAt: '', // 組織資料最後更新時間
      createdAt: '' // 組織創建時間
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
  gap: 30px;
}

.org-avatar img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.org-details h2 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.description {
  color: #f1eded;
  margin: 20px 0 20px 0;
  font-size: 18px;
}

.meta-info {
  color: #888;
  font-size: 18px;
}

.meta-info p {
  margin: 10px 0;
  color: #f1eded;
}
</style>
