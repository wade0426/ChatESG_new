<template>
  <Sidebar :isOpen="uiState.isSidebarOpen" @close="navigationControls.closeNav" />
  <Header @openNav="navigationControls.openNav" />
  
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
                <button class="edit-btn" @click="uiState.showUsernameModal = true">
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
          <button class="modify-btn" @click="uiState.showPasswordModal = true">修改</button>
        </div>
      </div>

      <div class="info-group">
          <label>所屬組織</label>
          <div class="info-value">{{ userInfo.organizationName }}</div>
      </div>

      <div class="info-group">
        <label>組織角色</label>
        <div class="info-value">{{ userInfo.organizationRole }}</div>
      </div>

      <div class="info-group">
        <label>Email</label>
        <div class="info-value">{{ userInfo.email }}</div>
      </div>
    </div>

    <!-- 密碼修改彈出框 -->
    <div v-if="uiState.showPasswordModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>修改密碼</h2>
          <button class="close-btn" @click="closePasswordModal">×</button>
        </div>
        <form @submit.prevent="submitPasswordChange" class="modal-body">
          <div class="form-group" style="display: none;">
            <label for="username">用戶名</label>
            <input 
              type="text"
              id="username" 
              name="username" 
              :value="userInfo.userName"
              autocomplete="username"
              readonly
            />
          </div>
          <div class="form-group">
            <label for="currentPassword">目前密碼</label>
            <input 
              id="currentPassword"
              type="password" 
              v-model="forms.password.currentPassword" 
              placeholder="請輸入目前密碼"
              autocomplete="current-password"
            />
          </div>
          <div class="form-group">
            <label for="newPassword">新密碼</label>
            <input 
              id="newPassword"
              type="password" 
              v-model="forms.password.newPassword" 
              placeholder="請輸入新密碼"
              autocomplete="new-password"
            />
          </div>
          <div class="form-group">
            <label for="confirmPassword">確認新密碼</label>
            <input 
              id="confirmPassword"
              type="password" 
              v-model="forms.password.confirmPassword" 
              placeholder="請再次輸入新密碼"
              autocomplete="new-password"
            />
          </div>
          <div class="error-message" v-if="uiState.passwordError">{{ uiState.passwordError }}</div>
          <div class="modal-footer">
            <button type="button" class="cancel-btn" @click="closePasswordModal">取消</button>
            <button type="submit" class="save-btn" :disabled="uiState.isSubmittingPassword">確定修改</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 姓名修改彈出框 -->
    <div v-if="uiState.showUsernameModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>修改姓名</h2>
          <button class="close-btn" @click="closeUsernameModal">×</button>
        </div>
        <form @submit.prevent="submitUsernameChange" class="modal-body">
          <div class="form-group">
            <label for="newUsername">新姓名</label>
            <input 
              id="newUsername"
              type="text" 
              v-model="forms.username.newUsername" 
              placeholder="請輸入新姓名"
            />
          </div>
          <div class="error-message" v-if="uiState.usernameError">{{ uiState.usernameError }}</div>
          <div class="modal-footer">
            <button type="button" class="cancel-btn" @click="closeUsernameModal">取消</button>
            <button type="submit" class="save-btn" :disabled="uiState.isSubmittingUsername">確定修改</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch, reactive } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import { useUserStore } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'

// 表单验证工具函数
const validatePassword = (form) => {
  if (!form.currentPassword || !form.newPassword || !form.confirmPassword) {
    return '請填寫所有欄位'
  }
  if (form.newPassword !== form.confirmPassword) {
    return '新密碼與確認密碼不符'
  }
  if (form.newPassword.length < 6) {
    return '新密碼長度至少需要6個字符'
  }
  return ''
}

export default {
  name: 'UserProfile',
  components: {
    Sidebar,
    Header
  },
  setup() {
    const userStore = useUserStore()
    const router = useRouter()
    const route = useRoute()

    // 使用reactive管理表單狀態
    const forms = reactive({
      password: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      username: {
        newUsername: ''
      }
    })

    // 統一管理UI狀態
    const uiState = reactive({
      isSidebarOpen: false,
      showPasswordModal: false,
      showUsernameModal: false,
      isSubmittingPassword: false,
      isSubmittingUsername: false,
      passwordError: '',
      usernameError: ''
    })

    // 緩存用戶信息計算屬性
    const userInfo = computed(() => ({
      userName: userStore.username,
      userID: userStore.userID,
      avatarUrl: userStore.avatarUrl,
      email: userStore.email,
      organizationName: userStore.organizationName,
      organizationRole: userStore.organizationRole
    }))

    const defaultAvatar = 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png'

    // 初始化函數
    const initializeUser = async () => {
      if (!userStore.isAuthenticated) {
        userStore.initializeFromStorage()
        if (!userStore.isAuthenticated) {
          router.push('/login')
          return
        }
      }
      await userStore.fetchUserProfile()
    }

    // 導航控制
    const navigationControls = {
      openNav: () => uiState.isSidebarOpen = true,
      closeNav: () => uiState.isSidebarOpen = false
    }

    // 模態框控制
    const modalControls = {
      closePasswordModal: () => {
        uiState.showPasswordModal = false
        forms.password = {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
        uiState.passwordError = ''
      },
      closeUsernameModal: () => {
        uiState.showUsernameModal = false
        forms.username.newUsername = ''
        uiState.usernameError = ''
      }
    }

    // 表單提交處理
    const submitHandlers = {
      async submitPasswordChange() {
        const validationError = validatePassword(forms.password)
        if (validationError) {
          uiState.passwordError = validationError
          return
        }

        try {
          uiState.isSubmittingPassword = true
          const result = await userStore.updatePassword(
            forms.password.currentPassword,
            forms.password.newPassword
          )

          if (result.success) {
            alert('密碼修改成功')
            modalControls.closePasswordModal()
          } else {
            uiState.passwordError = result.error
          }
        } catch (error) {
          uiState.passwordError = '發生錯誤，請稍後再試'
        } finally {
          uiState.isSubmittingPassword = false
        }
      },

      async submitUsernameChange() {
        if (!forms.username.newUsername) {
          uiState.usernameError = '請填寫新姓名'
          return
        }

        try {
          uiState.isSubmittingUsername = true
          const result = await userStore.updateUsername(forms.username.newUsername)

          if (result.success) {
            alert('姓名修改成功')
            modalControls.closeUsernameModal()
          } else {
            uiState.usernameError = result.error
          }
        } catch (error) {
          uiState.usernameError = '發生錯誤，請稍後再試'
        } finally {
          uiState.isSubmittingUsername = false
        }
      }
    }

    // 生命周期钩子
    onMounted(async () => {
      await initializeUser()
    })

    // 路由监听
    watch(
      () => route.fullPath,
      async () => {
        await initializeUser()
      }
    )

    return {
      userInfo,
      defaultAvatar,
      uiState,
      forms,
      navigationControls,
      modalControls,
      closePasswordModal: modalControls.closePasswordModal,
      closeUsernameModal: modalControls.closeUsernameModal,
      ...submitHandlers
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
