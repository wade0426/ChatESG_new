<template>
    <div class="report-management">
      <div class="page-header">
        <h1>報告書管理</h1>
      </div>
      <div class="report-list">
        <div class="report-card">
          <p>這是報告書管理頁面</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'ReportManagement'
  }
  </script>
  
  <style scoped>
  .report-management {
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
  
  .report-list {
    background-color: #2c2c2c;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  </style> 