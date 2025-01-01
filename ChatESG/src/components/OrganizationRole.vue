<template>
  <div class="organization-role">
    <div class="page-header">
      <h1>身份組</h1>
      <button class="add-btn">新增身份組</button>
    </div>
    <div class="role-list">
      <div class="role-card">
        <p>這是身份組頁面</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OrganizationRole'
}
</script>

<style scoped>
.organization-role {
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
}

.add-btn {
  padding: 8px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.add-btn:hover {
  background-color: #0056b3;
}

.role-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style> 