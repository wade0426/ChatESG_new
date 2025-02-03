<template>
  <div class="modal" v-if="isVisible">
    <div class="modal-content">
      <h2>建立公司基本資料</h2>
      
      <form @submit.prevent="submitForm">
        <!-- 輸入公司基本資料名稱 -->
        <div class="form-group">
          <label for="companyInfoName">公司基本資料名稱</label>
          <input 
            id="companyInfoName" 
            v-model="formData.companyInfoName" 
            type="text" 
            placeholder="輸入公司基本資料名稱"
            :class="{ 'error': errors.companyInfoName }"
            :disabled="isSubmitting"
          />
          <span class="error-message" v-if="errors.companyInfoName">{{ errors.companyInfoName }}</span>
        </div>

        <!-- 選擇產業 -->
        <div class="form-group">
          <label for="industrySelect">產業類別</label>
          <select 
            id="industrySelect" 
            v-model="formData.selectedIndustry"
            :class="{ 'error': errors.selectedIndustry }"
            :disabled="isSubmitting"
          >
            <option value="">請選擇產業</option>
            <option 
              v-for="industry in companyStore.industries" 
              :value="industry.name" 
              :key="industry.name"
            >
              {{ industry.name }}
            </option>
          </select>
          <span class="error-message" v-if="errors.selectedIndustry">{{ errors.selectedIndustry }}</span>
        </div>

        <div class="modal-footer">
          <button type="button" @click="hideModal" :disabled="isSubmitting">取消</button>
          <button type="submit" :disabled="isSubmitting">
            <span v-if="isSubmitting">處理中...</span>
            <span v-else>確認</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useUserStore } from '../stores/user'
import { useCompanyStore } from '../stores/company'
import { useFormValidation } from '../composables/useFormValidation'
import { useToast } from 'vue-toastification'

const userStore = useUserStore()
const companyStore = useCompanyStore()
const toast = useToast()

const isVisible = ref(false)
const isSubmitting = ref(false)

const formData = reactive({
  companyInfoName: "",
  selectedIndustry: ""
})

const { errors, validateForm } = useFormValidation({
  rules: {
    companyInfoName: [
      { required: true, message: '請輸入公司基本資料名稱' },
      { max: 100, message: '公司基本資料表名稱不可超過100個字' }
    ],
    selectedIndustry: [
      { required: true, message: '請選擇產業類別' }
    ]
  }
})

const showModal = () => {
  isVisible.value = true
}

const hideModal = () => {
  isVisible.value = false
  resetForm()
}

const resetForm = () => {
  formData.companyInfoName = ""
  formData.selectedIndustry = ""
  Object.keys(errors).forEach(key => errors[key] = '')
  isSubmitting.value = false
}

const submitForm = async () => {
  if (!validateForm(formData)) return
  
  try {
    isSubmitting.value = true
    await companyStore.createCompanyInfo({
      name: formData.companyInfoName,
      industry: formData.selectedIndustry,
      creator: userStore.userID,
      organizationID: userStore.organizationID
    })
    
    toast.success('公司基本資料建立成功')
    hideModal()
  } catch (error) {
    toast.error(error.message || '建立失敗，請稍後再試')
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({
  showModal
})
</script>

<style scoped>
@import '../styles/modal.css';
@import '../styles/form.css';

.form-group {
  margin-bottom: 1rem;
}

.modal-footer button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style> 