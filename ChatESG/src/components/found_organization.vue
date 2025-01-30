<!-- 創建組織組件 -->
<template>
  <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
  <Header @openNav="openNav" />
  <div class="found-organization">
    <div class="organization-container">
      <h1 class="title">創建新組織</h1>
      <form @submit.prevent="handleSubmit" class="organization-form">
        <div class="form-group">
          <label for="organizationName">組織名稱</label>
          <input
            type="text"
            id="organizationName"
            v-model="formData.organizationName"
            required
            :maxlength="50"
            placeholder="請輸入組織名稱（2-50字）"
            class="form-input"
            @input="validateOrganizationName"
          />
          <span class="error-message" v-if="errors.organizationName">{{ errors.organizationName }}</span>
        </div>

        <div class="form-group">
          <label for="organizationDescription">組織描述</label>
          <textarea
            id="organizationDescription"
            v-model="formData.organizationDescription"
            placeholder="請簡短描述您的組織"
            class="form-textarea"
            rows="4"
          ></textarea>
        </div>

        <div class="form-group">
          <label for="organizationLogo">組織標誌 (最大2MB，支持jpg、png格式)</label>
          <div class="logo-upload">
            <img :src="previewImage || defaultLogo" class="logo-preview" alt="組織標誌預覽" />
            <input
              type="file"
              id="organizationLogo"
              @change="handleImageUpload"
              accept="image/*"
              class="file-input"
            />
            <button type="button" class="upload-btn" @click="triggerFileInput">
              上傳標誌
            </button>
          </div>
        </div>

        <button type="submit" class="submit-btn" :disabled="isSubmitting">
          {{ isSubmitting ? '創建中...' : '創建組織' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import debounce from 'lodash/debounce'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const router = useRouter()
const isSidebarOpen = ref(false)
const userStore = useUserStore()

const openNav = () => {
  isSidebarOpen.value = true
}

const closeNav = () => {
  isSidebarOpen.value = false
}

const isSubmitting = ref(false)
const defaultLogo = 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/organization.png'
const previewImage = ref(null)

const formData = ref({
  organizationName: '',
  organizationDescription: '',
  avatarUrl: ''
})

const errors = ref({
  organizationName: '',
  organizationDescription: '',
  avatarUrl: ''
})

const validateOrganizationName = debounce(() => {
  if (formData.value.organizationName.length < 2) {
    errors.value.organizationName = '組織名稱至少需要2個字符'
  } else if (formData.value.organizationName.length > 50) {
    errors.value.organizationName = '組織名稱不能超過50個字符'
  } else {
    errors.value.organizationName = ''
  }
}, 300)

const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    // 驗證文件大小
    if (file.size > 2 * 1024 * 1024) {
      errors.value.avatarUrl = '圖片大小不能超過2MB'
      return
    }
    
    // 驗證文件類型
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      errors.value.avatarUrl = '只支持JPG和PNG格式的圖片'
      return
    }

    // 壓縮圖片
    try {
      const compressedFile = await compressImage(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        previewImage.value = e.target.result
        formData.value.avatarUrl = e.target.result
        errors.value.avatarUrl = ''
      }
      reader.readAsDataURL(compressedFile)
    } catch (error) {
      errors.value.avatarUrl = '圖片處理失敗'
    }
  }
}

const compressImage = (file) => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.src = URL.createObjectURL(file)
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const maxWidth = 800
      let width = img.width
      let height = img.height

      if (width > maxWidth) {
        height = (maxWidth * height) / width
        width = maxWidth
      }

      canvas.width = width
      canvas.height = height
      ctx.drawImage(img, 0, 0, width, height)

      canvas.toBlob((blob) => {
        resolve(new File([blob], file.name, { type: file.type }))
      }, file.type, 0.8)
    }
    img.onerror = reject
  })
}

const triggerFileInput = () => {
  document.getElementById('organizationLogo').click()
}

const handleSubmit = async () => {
  // 验证表单
  if (!validateForm()) {
    return
  }

  try {
    isSubmitting.value = true
    const response = await fetch('http://localhost:8000/api/organizations/found', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        organizationName: formData.value.organizationName.trim(),
        organizationDescription: formData.value.organizationDescription.trim(),
        avatarUrl: formData.value.avatarUrl,
        user_id: userStore.userID
      })
    })

    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || '創建組織失敗')
    }

    showNotification('success', '組織創建成功！')
    router.push('/dashboard')
  } catch (error) {
    console.error('創建組織失敗:', error)
    showNotification('error', error.message)
  } finally {
    isSubmitting.value = false
  }
}

const validateForm = () => {
  let isValid = true
  
  // 验证组织名称
  if (!formData.value.organizationName.trim()) {
    errors.value.organizationName = '請輸入組織名稱'
    isValid = false
  }

  // 验证组织描述
  if (formData.value.organizationDescription.length > 500) {
    errors.value.organizationDescription = '組織描述不能超過500個字符'
    isValid = false
  }

  return isValid
}

const showNotification = (type, message) => {
  // 这里可以集成你喜欢的通知组件
  if (type === 'error') {
    console.error(message)
  } else {
    console.log(message)
  }
}
</script>

<style scoped>
.found-organization {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #000000;
  padding: 2rem;
}

.organization-container {
  background-color: #1c1c1e;
  border-radius: 20px;
  padding: 2.5rem;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 2rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 2rem;
  text-align: center;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #ffffff;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d2d2d7;
  border-radius: 12px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
  background-color: #1c1c1e;
  color: #ffffff;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #0071e3;
}

.logo-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.logo-preview {
  width: 120px;
  height: 120px;
  border-radius: 60px;
  object-fit: cover;
  border: 2px solid #d2d2d7;
}

.file-input {
  display: none;
}

.upload-btn {
  padding: 0.5rem 1rem;
  background-color: #f5f5f7;
  border: none;
  border-radius: 8px;
  color: #1d1d1f;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s ease;
}

.upload-btn:hover {
  background-color: #e8e8ed;
}

.submit-btn {
  width: 100%;
  padding: 1rem;
  background-color: #0071e3;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.submit-btn:hover {
  background-color: #0077ed;
}

.submit-btn:disabled {
  background-color: #999;
  cursor: not-allowed;
}

.error-message {
  color: #ff3b30;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 1rem;
  border-radius: 8px;
  z-index: 1000;
}

.notification.success {
  background-color: #34c759;
  color: white;
}

.notification.error {
  background-color: #ff3b30;
  color: white;
}

@media (max-width: 768px) {
  .organization-container {
    padding: 1.5rem;
  }
  
  .title {
    font-size: 1.5rem;
  }
}
</style>