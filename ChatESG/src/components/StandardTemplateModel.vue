<template>
  <div class="modal" v-if="isVisible">
    <div class="modal-content">
      <h2>建立準則模板</h2>
      
      <!-- 輸入準則模板名稱 -->
      <label for="templateName">準則模板名稱</label>
      <input 
        id="templateName" 
        v-model="templateName" 
        type="text" 
        placeholder="輸入準則模板名稱"
        :class="{ 'error': errors.templateName }"
      />
      <span class="error-message" v-if="errors.templateName">{{ errors.templateName }}</span>

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
import { useToast } from 'vue-toastification'

const emit = defineEmits(['template-created'])
const userStore = useUserStore()
const toast = useToast()

const isVisible = ref(false)
const templateName = ref("")
const selectedIndustry = ref("")
const industries = ref(["金融業", "科技業", "製造業"])

// 錯誤訊息物件
const errors = reactive({
  templateName: '',
  selectedIndustry: ''
})

// 驗證表單
const validateForm = () => {
  let isValid = true
  
  // 重置錯誤訊息
  errors.templateName = ''
  errors.selectedIndustry = ''

  // 驗證準則模板名稱
  if (!templateName.value.trim()) {
    errors.templateName = '請輸入準則模板名稱'
    isValid = false
  } else if (templateName.value.length > 100) {
    errors.templateName = '準則模板名稱不可超過100個字'
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
  templateName.value = ""
  selectedIndustry.value = ""
  errors.templateName = ''
  errors.selectedIndustry = ''
}

const submitForm = async () => {
  if (validateForm()) {
    try {
      const response = await fetch('http://localhost:8000/api/organizations/create_standard_template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          organization_id: userStore.organizationID,
          creator_id: userStore.userID,
          template_name: templateName.value,
          category: selectedIndustry.value,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        toast.success('準則模板創建成功');
        hideModal();
        // 如果需要，可以在這裡觸發更新列表的事件
        emit('template-created', result.data);
      } else {
        throw new Error(result.detail || '創建準則模板失敗');
      }
    } catch (error) {
      toast.error(error.message || '創建準則模板失敗');
      console.log(error)
    }
  }
}

defineExpose({
  showModal
})
</script>
  
<style scoped>
@import '../styles/modal.css';
@import '../styles/form.css';

/* 只保留特定的樣式覆蓋 */
.error-message {
  color: red;
  font-size: 12px;
  margin-top: 5px;
}

.modal-content input.error,
.modal-content select.error {
  border: 1px solid red;
}
</style> 