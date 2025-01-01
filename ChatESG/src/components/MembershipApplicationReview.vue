<template>
    <div class="membership-application-review">
      <div class="page-header">
        <h1>人員申請審核</h1>
      </div>
      <div class="application-list">
        <div class="application-card">
          <p>這是申請審核頁面</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'MembershipApplicationReview'
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
  }
  
  .application-list {
    background-color: #2c2c2c;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  </style> 