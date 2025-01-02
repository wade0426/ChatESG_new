<template>
    <div class="modal" v-if="isVisible">
      <div class="modal-content">
        <h2>加入組織</h2>
        
        <!-- 輸入組織ID -->
        <label for="organizationId">組織ID</label>
        <input 
          id="organizationId" 
          v-model="organizationId" 
          type="text" 
          placeholder="請輸入8位數組織ID"
          :class="{ 'error': errors.organizationId }"
          maxlength="8"
        />
        <span class="error-message" v-if="errors.organizationId">{{ errors.organizationId }}</span>
  
        <div class="modal-footer">
          <button @click="hideModal">取消</button>
          <button @click="submitForm">確認</button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, reactive } from 'vue'
  import { useUserStore } from '../stores/user'
  
  const userStore = useUserStore()
  const isVisible = ref(false)
  const organizationId = ref("")
  
  // 錯誤訊息物件
  const errors = reactive({
    organizationId: ''
  })
  
  // 驗證表單
  const validateForm = () => {
    let isValid = true
    errors.organizationId = ''
  
    // 驗證組織ID格式
    const idPattern = /^[A-Za-z0-9]{8}$/
    if (!organizationId.value) {
      errors.organizationId = '請輸入組織ID'
      isValid = false
    } else if (!idPattern.test(organizationId.value)) {
      errors.organizationId = '組織ID必須為8位英文或數字'
      isValid = false
    }
  
    return isValid
  }
  
  const showModal = () => {
    isVisible.value = true
  }
  
  const hideModal = () => {
    isVisible.value = false
    // 重置表單和錯誤訊息
    organizationId.value = ""
    errors.organizationId = ''
  }
  
  const submitForm = () => {
    if (validateForm()) {
      // 呼叫 API 加入組織
      fetch('http://localhost:8000/api/organizations/join', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userStore.userID,
          organization_code: organizationId.value
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          alert('成功加入組織！')
          hideModal()
          // 重新加載用戶資料
          userStore.fetchUserProfile()
        } else {
          errors.organizationId = data.detail || '加入組織失敗'
        }
      })
      .catch(error => {
        console.error('Error:', error)
        errors.organizationId = '加入組織時發生錯誤'
      })
    }
  }
  
  defineExpose({
    showModal
  })
  </script>
  
  <style scoped>
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .modal-content {
    background-color: #242526;
    padding: 20px;
    border-radius: 8px;
    min-width: 400px;
    color: white;
  }
  
  .modal-footer {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 10px;
  }
  
  .modal-footer button:nth-child(1) {
    background-color: #f44336;
  }
  
  .modal-footer button:nth-child(2) {
    background-color: #4CAF50;
  }
  
  button {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    background-color: #3A3B3C;
    color: white;
  }
  
  button:hover {
    background-color: #4A4B4C;
  }
  
  .modal-content label {
    display: block;
    margin: 10px 0 5px;
    text-align: left;
  }
  
  .modal-content input {
    width: 100%;
    padding: 8px;
    margin-bottom: 10px;
    background-color: #3A3B3C;
    border: none;
    color: white;
    border-radius: 4px;
  }
  
  .error-message {
    color: red;
    font-size: 12px;
    margin-top: 5px;
  }
  
  .modal-content input.error {
    border: 1px solid red;
  }
  </style>