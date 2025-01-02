<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="org-avatar">
        <img src="https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/organization.png" alt="Organization Avatar" class="avatar-img">
      </div>
      <h2 class="org-name">組織名稱</h2>
    </div>
    <nav class="sidebar-nav">
      <router-link to="/organization/details" class="nav-item" :class="{ active: $route.path === '/organization/details' }">
        <i class="fas fa-info-circle"></i>
        組織詳細資訊
      </router-link>
      <router-link to="/organization/report-management" class="nav-item" :class="{ active: $route.path === '/organization/report-management' }">
        <i class="fas fa-file-alt"></i>
        報告書管理
      </router-link>
      <router-link to="/organization/membership-application-review" class="nav-item" :class="{ active: $route.path === '/organization/membership-application-review' }">
        <i class="fas fa-user-plus"></i>
        人員申請審核
      </router-link>
      <router-link to="/organization/roles" class="nav-item" :class="{ active: $route.path === '/organization/roles' }">
        <i class="fas fa-user-tag"></i>
        身份組
      </router-link>
      <router-link to="/organization/members" class="nav-item" :class="{ active: $route.path === '/organization/members' }">
        <i class="fas fa-users"></i>
        組織成員
      </router-link>
      <router-link to="/organization/permissions" class="nav-item" :class="{ active: $route.path === '/organization/permissions' }">
        <i class="fas fa-lock"></i>
        權限
      </router-link>
      <router-link to="/organization/payment" class="nav-item" :class="{ active: $route.path === '/organization/payment' }">
        <i class="fas fa-credit-card"></i>
        付款與方案
      </router-link>
      <router-link to="/organization/purchases" class="nav-item" :class="{ active: $route.path === '/organization/purchases' }">
        <i class="fas fa-shopping-cart"></i>
        購買記錄
      </router-link>
      <router-link to="/organization/audit-log" class="nav-item" :class="{ active: $route.path === '/organization/audit-log' }">
        <i class="fas fa-history"></i>
        操作日誌
      </router-link>
    </nav>
  </div>
</template>

<script>
export default {
  name: 'OrganizationSidebar'
}
</script>

<style scoped>
.sidebar {
  width: 250px;
  height: 100vh;
  /* background-color: #2c2c2c; */
  background-color: #18191A;
  color: white;
  padding: 20px 0;
  /* 加入右邊的邊框 */
  border-right: 2px solid #3a3a3a;
}

.sidebar-header {
  padding: 0 20px;
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.org-avatar {
  margin-bottom: 0;
}

.avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: block;
}

.org-name {
  font-size: 1.2rem;
  margin: 0;
  flex: 1;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
}

.nav-item {
  padding: 12px 20px;
  color: #ffffff;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-item:hover {
  background-color: #3a3a3a;
}

.nav-item.active {
  background-color: #4a4a4a;
}

.nav-item i {
  width: 20px;
}
</style>
