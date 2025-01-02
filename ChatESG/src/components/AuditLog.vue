<template>
  <div class="audit-log">
    <div class="page-header">
      <h1>日誌紀錄</h1>
    </div>
    <div class="audit-log-list">
      <div class="audit-log-card">
        <p>這是日誌紀錄頁面</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuditLog'
}
</script>

<style scoped>
.audit-log {
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

.audit-log-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style> 