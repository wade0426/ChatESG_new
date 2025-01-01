<template>
  <div class="purchase-record">
    <div class="page-header">
      <h1>購買記錄</h1>
    </div>
    <div class="record-list">
      <div class="record-card">
        <p>這是購買記錄頁面</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PurchaseRecord'
}
</script>

<style scoped>
.purchase-record {
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

.record-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style> 