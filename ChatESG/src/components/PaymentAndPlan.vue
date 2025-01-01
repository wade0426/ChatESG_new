<template>
  <div class="payment-and-plan">
    <div class="page-header">
      <h1>付款與方案</h1>
    </div>
    <div class="plan-list">
      <div class="plan-card">
        <p>這是付款與方案頁面</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaymentAndPlan'
}
</script>

<style scoped>
.payment-and-plan {
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

.plan-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style> 