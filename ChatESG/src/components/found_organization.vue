<!-- 創建組織組件 -->
<template>
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
            placeholder="請輸入組織名稱"
            class="form-input"
          />
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
          <label for="organizationLogo">組織標誌</label>
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

const router = useRouter()
const isSubmitting = ref(false)
const defaultLogo = 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/organization.png'
const previewImage = ref(null)

const formData = ref({
  organizationName: '',
  organizationDescription: '',
  avatarUrl: ''
})

const handleImageUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      previewImage.value = e.target.result
      formData.value.avatarUrl = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const triggerFileInput = () => {
  document.getElementById('organizationLogo').click()
}

const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    const response = await fetch('http://localhost:8000/api/organizations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        organizationName: formData.value.organizationName,
        organizationDescription: formData.value.organizationDescription,
        avatarUrl: formData.value.avatarUrl
      })
    })

    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || '創建組織失敗')
    }

    // 成功後顯示提示並跳轉
    alert('組織創建成功！')
    router.push('/dashboard')
  } catch (error) {
    console.error('創建組織失敗:', error)
    alert(error.message)
  } finally {
    isSubmitting.value = false
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

@media (max-width: 768px) {
  .organization-container {
    padding: 1.5rem;
  }
  
  .title {
    font-size: 1.5rem;
  }
}
</style>

