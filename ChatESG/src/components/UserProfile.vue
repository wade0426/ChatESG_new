<template>
  <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
  <Header @openNav="openNav" />
  
  <div class="profile-container">
    <div class="profile-header">
      <div class="profile-avatar">
        <img :src="userInfo.avatarUrl || defaultAvatar" alt="用戶頭像" />
        <button class="upload-btn">上傳頭像</button>
      </div>
      <h1>基本資訊</h1>
    </div>
    
    <div class="profile-content">
        <div class="info-group">
            <label>姓名</label>
            <div class="info-value">
                {{ userInfo.userName }}
                <button class="edit-btn" @click="showUsernameModal = true">
                    <i class="fas fa-pencil-alt"></i>
                </button>
            </div>
        </div>
        
        <div class="info-group">
          <label>UUID</label>
          <div class="info-value">{{ userInfo.userID }}</div>
        </div>
    
        <!-- <div class="info-group">
        <label>目前頭像</label>
        <div class="info-value">
          <img :src="userInfo.avatarUrl || defaultAvatar" alt="當前頭像" class="current-avatar" />
        </div>
      </div> -->

      <div class="info-group">
        <label>密碼</label>
        <div class="info-value">
          <button class="modify-btn" @click="showPasswordModal = true">修改</button>
        </div>
      </div>

      <div class="info-group">
          <label>所屬組織</label>
          <div class="info-value">{{ userInfo.organizationName }}</div>
      </div>

      <div class="info-group">
        <label>組織角色</label>
        <div class="info-value">一般用戶</div>
      </div>

      <div class="info-group">
        <label>Email</label>
        <div class="info-value">{{ userInfo.email }}</div>
      </div>
    </div>

    <!-- 姓名修改彈出框 -->
    <div v-if="showUsernameModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>修改姓名</h2>
          <button class="close-btn" @click="closeUsernameModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>新姓名</label>
            <input type="text" v-model="usernameForm.newUsername" placeholder="請輸入新姓名" />
          </div>
          <div class="error-message" v-if="usernameErrorMessage">{{ usernameErrorMessage }}</div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeUsernameModal">取消</button>
          <button class="save-btn" @click="submitUsernameChange" :disabled="isSubmittingUsername">確定修改</button>
        </div>
      </div>
    </div>

    <!-- 密碼修改彈出框 -->
    <div v-if="showPasswordModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>修改密碼</h2>
          <button class="close-btn" @click="closePasswordModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>目前密碼</label>
            <input type="password" v-model="passwordForm.currentPassword" placeholder="請輸入目前密碼" />
          </div>
          <div class="form-group">
            <label>新密碼</label>
            <input type="password" v-model="passwordForm.newPassword" placeholder="請輸入新密碼" />
          </div>
          <div class="form-group">
            <label>確認新密碼</label>
            <input type="password" v-model="passwordForm.confirmPassword" placeholder="請再次輸入新密碼" />
          </div>
          <div class="error-message" v-if="errorMessage">{{ errorMessage }}</div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closePasswordModal">取消</button>
          <button class="save-btn" @click="submitPasswordChange" :disabled="isSubmitting">確定修改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

export default {
  name: 'UserProfile',
  //   引入組件
  components: {
    Sidebar,
    Header
  },
  setup() {
    const isSidebarOpen = ref(false)
    const userInfo = ref({
      userName: '',
      userID: '',
      avatarUrl: '',
      email: '',
      organizationName: ''
    })

    const openNav = () => {
      isSidebarOpen.value = true
    }

    const closeNav = () => {
      isSidebarOpen.value = false
    }

    const showPasswordModal = ref(false)
    const errorMessage = ref('')
    const isSubmitting = ref(false)
    const passwordForm = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    const defaultAvatar = 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png'

    const getUserProfile = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/user/profile/Personal_Information', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_id: sessionStorage.getItem('userID')
          })
        })
        const data = await response.json()
        if (data.status === 'success') {
          userInfo.value = data.data
        } else {
          console.error('獲取用戶資料失敗')
        }
      } catch (error) {
        console.error('獲取用戶資料失敗:', error)
      }
    }

    const closePasswordModal = () => {
      showPasswordModal.value = false
      passwordForm.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      errorMessage.value = ''
    }

    const submitPasswordChange = async () => {
      // 驗證表單
      if (!passwordForm.value.currentPassword || !passwordForm.value.newPassword || !passwordForm.value.confirmPassword) {
        errorMessage.value = '請填寫所有欄位'
        return
      }

      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        errorMessage.value = '新密碼與確認密碼不符'
        return
      }

      if (passwordForm.value.newPassword.length < 6) {
        errorMessage.value = '新密碼長度至少需要6個字符'
        return
      }

      try {
        isSubmitting.value = true
        const response = await fetch('http://localhost:8000/api/user/profile/Change_Password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_id: sessionStorage.getItem('userID'),
            current_password: passwordForm.value.currentPassword,
            new_password: passwordForm.value.newPassword
          })
        })

        const data = await response.json()
        if (data.status === 'success') {
          alert('密碼修改成功')
          closePasswordModal()
        } else {
          errorMessage.value = data.detail || '密碼修改失敗'
        }
      } catch (error) {
        errorMessage.value = '發生錯誤，請稍後再試'
        console.error('密碼修改失敗:', error)
      } finally {
        isSubmitting.value = false
      }
    }

    const showUsernameModal = ref(false)
    const usernameErrorMessage = ref('')
    const isSubmittingUsername = ref(false)
    const usernameForm = ref({
      newUsername: ''
    })

    const closeUsernameModal = () => {
      showUsernameModal.value = false
      usernameForm.value = {
        newUsername: ''
      }
      usernameErrorMessage.value = ''
    }

    const submitUsernameChange = async () => {
      // 驗證表單
      if (!usernameForm.value.newUsername) {
        usernameErrorMessage.value = '請填寫新姓名'
        return
      }

      try {
        isSubmittingUsername.value = true
        const response = await fetch('http://localhost:8000/api/user/profile/Change_Username', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_id: sessionStorage.getItem('userID'),
            new_username: usernameForm.value.newUsername
          })
        })

        const data = await response.json()
        if (data.status === 'success') {
          // 直接更新本地的用戶信息
          userInfo.value.userName = usernameForm.value.newUsername
          alert('姓名修改成功')
          closeUsernameModal()
        } else {
          usernameErrorMessage.value = data.detail || '姓名修改失敗'
        }
      } catch (error) {
        usernameErrorMessage.value = '發生錯誤，請稍後再試'
        console.error('姓名修改失敗:', error)
      } finally {
        isSubmittingUsername.value = false
      }
    }

    onMounted(() => {
      getUserProfile()
    })

    return {
      userInfo,
      defaultAvatar,
      showPasswordModal,
      passwordForm,
      errorMessage,
      isSubmitting,
      closePasswordModal,
      submitPasswordChange,
      isSidebarOpen,
      openNav,
      closeNav,
      showUsernameModal,
      usernameForm,
      usernameErrorMessage,
      isSubmittingUsername,
      closeUsernameModal,
      submitUsernameChange
    }
  }
}
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 30px;
  background-color: #1c1c1e;
  border-radius: 20px;
  box-shadow: 0 2px 20px rgba(255, 255, 255, 0.1);
}

.profile-header {
  text-align: center;
  margin-bottom: 40px;
}

.profile-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin-top: 20px;
}

.profile-avatar {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto;
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #0a84ff;
}

.upload-btn {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #0a84ff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 15px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.upload-btn:hover {
  background-color: #007aff;
}

.profile-content {
  display: grid;
  gap: 20px;
}

.info-group {
  display: grid;
  grid-template-columns: 120px 1fr;
  align-items: center;
  padding: 15px;
  background-color: #2c2c2e;
  border-radius: 12px;
}

.info-group label {
  color: #8e8e93;
  font-size: 16px;
}

.info-value {
  color: white;
  font-size: 16px;
}

.current-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
}

.modify-btn {
  background-color: #0a84ff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.modify-btn:hover {
  background-color: #007aff;
}

/* 新增的 Modal 相關樣式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #1c1c1e;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  padding: 20px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h2 {
  color: white;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #8e8e93;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  color: #8e8e93;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #3a3a3c;
  background-color: #2c2c2e;
  color: white;
}

.error-message {
  color: #ff453a;
  margin-top: 10px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn, .save-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background-color: #3a3a3c;
  color: white;
}

.save-btn {
  background-color: #0a84ff;
  color: white;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.edit-btn {
  background: none;
  border: none;
  color: #0a84ff;
  padding: 4px 8px;
  margin-left: 8px;
  cursor: pointer;
  transition: color 0.3s;
}

.edit-btn:hover {
  color: #007aff;
}

.edit-btn i {
  font-size: 16px;
}
</style>
