<template>
  <div class="modal" v-if="isVisible">
    <div class="modal-content">
      <h2>建立公司基本資料</h2>
      
      <!-- 輸入公司基本資料名稱 -->
      <label for="companyInfoName">公司基本資料名稱</label>
      <input 
        id="companyInfoName" 
        v-model="companyInfoName" 
        type="text" 
        placeholder="輸入公司基本資料名稱"
        :class="{ 'error': errors.companyInfoName }"
      />
      <span class="error-message" v-if="errors.companyInfoName">{{ errors.companyInfoName }}</span>

      <!-- 選擇產業 -->
      <label for="industrySelect">產業類別</label>
      <select 
        id="industrySelect" 
        v-model="selectedIndustry"
        :class="{ 'error': errors.selectedIndustry }"
      >
        <option value="">請選擇產業</option>
        <option v-for="industry in industries" :value="industry" :key="industry">{{ industry }}</option>
      </select>
      <span class="error-message" v-if="errors.selectedIndustry">{{ errors.selectedIndustry }}</span>

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
const companyInfoName = ref("")
const selectedIndustry = ref("")
const industries = ref(["金融業", "科技業", "製造業"])

// 錯誤訊息物件
const errors = reactive({
  companyInfoName: '',
  selectedIndustry: ''
})

// 驗證表單
const validateForm = () => {
  let isValid = true
  
  // 重置錯誤訊息
  errors.companyInfoName = ''
  errors.selectedIndustry = ''

  // 驗證公司名稱
  if (!companyInfoName.value.trim()) {
    errors.companyInfoName = '請輸入公司基本資料名稱'
    isValid = false
  } else if (companyInfoName.value.length > 100) {
    errors.companyInfoName = '公司基本資料表名稱不可超過100個字'
    isValid = false
  }

  // 驗證產業選擇
  if (!selectedIndustry.value) {
    errors.selectedIndustry = '請選擇產業類別'
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
  companyInfoName.value = ""
  selectedIndustry.value = ""
  errors.companyInfoName = ''
  errors.selectedIndustry = ''
}

const submitForm = () => {
  if (validateForm()) {
    console.log("提交公司基本資料：", {
        name: companyInfoName.value,
        industry: selectedIndustry.value,
        // 建立人
        creator: userStore.userID,
        // 建立時間不需要 給 DB 自動產生
    })
    hideModal()
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
  /* 置中 */
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

.modal-content input,
.modal-content select {
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
  background-color: #3A3B3C;
  border: none;
  color: white;
  border-radius: 4px;
}

.modal-content select option {
  background-color: #242526;
}

.error-message {
  color: red;
  font-size: 12px;
  margin-top: 5px;
}

.modal-content input.error {
  border: 1px solid red;
}

.modal-content select.error {
  border: 1px solid red;
}

</style> 