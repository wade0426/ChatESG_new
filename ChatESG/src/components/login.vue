<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo-container">
        <img src="@/assets/logo_chatesg.png" alt="Logo" class="logo">
      </div>
      <h1 class="title">登入</h1>
      
      <div class="form-container">
        <input 
          type="text" 
          v-model="username" 
          placeholder="使用者名稱"
          class="input-field"
        >
        
        <input 
          type="password" 
          v-model="password" 
          placeholder="密碼"
          class="input-field"
        >
        
        <div class="remember-me">
          <input 
            type="checkbox" 
            v-model="rememberMe" 
            id="remember"
          >
          <label for="remember">記住我</label>
        </div>
        
        <button 
          @click="handleLogin" 
          class="login-button"
        >
          登入
        </button>
        
        <div class="links">
          <a href="#" class="forgot-password">忘記密碼?</a>
          <a href="/signup" class="create-account">建立新帳號</a>
        </div>
      </div>
    </div>
  </div>
  <div id="toast"
        style="display: none; position: fixed; top: 20px; right: 20px; padding: 15px 25px; border-radius: 5px; color: white; z-index: 1000;">
  </div>
</template>

<script>
// 導出模組默認內容，在一個文件中定義主要的功能或組件，可以被其他文件引用和使用。
import { useUserStore } from '@/stores/user'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

export default {
  // 定義組件名稱
  name: 'Login',

  // 使用組合式API設置Pinia store
  setup() {
    const userStore = useUserStore()
    return { userStore, configStore }
  },

  // 定義組件的響應式數據
  data() {
    return {
      username: '', // 用戶名
      password: '', // 密碼
      rememberMe: false, // 記住我選項
    }
  },

  // 組件掛載後執行初始化
  mounted() {
    this.init();
  },

  // 定義組件的方法
  methods: {
    // 處理登入邏輯的異步方法
    async handleLogin() {
      try {
        // 發送登入請求到後端API
        const response = await fetch(`${configStore.apiBaseUrl}/api/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: this.username,
            password: this.password
          })
        });

        // 解析響應數據
        const data = await response.json();
        
        // 檢查響應狀態
        if (!response.ok) {
          throw new Error(data.detail);
        }

        // 使用 Pinia store 更新登入狀態
        this.userStore.login(data.userID, data.username, data.access_token);
        
        // 顯示登入成功提示
        this.showToast('登入成功!', true);
        
        // 如果用戶選擇記住我，保存用戶名
        if(this.rememberMe) {
          sessionStorage.setItem('username', this.username);
        }
        
        // 等待一下確保狀態更新完成
        await this.$nextTick();
        
        // 登入成功後導航到首頁
        this.$router.push('/home');
        
      } catch (error) {
        // 處理錯誤情況
        this.showToast(error.message, false);
        this.password = ''; // 清空密碼欄位
      }
    },

    showToast(message, isSuccess) { //顯示提示訊息
      const toast = document.getElementById('toast');
      toast.textContent = message;
      toast.style.backgroundColor = isSuccess ? '#4CAF50' : '#f44336';
      toast.style.display = 'block';

      setTimeout(() => {
        toast.style.display = 'none';
      }, 3000);
    },

    init() { //初始化
      this.username = sessionStorage.getItem('username') || '';
      if (this.username) {
        this.rememberMe = true;
      }
    }
  }
}
</script>

<!-- scoped 用於限制樣式只影響此元件 -->
<style scoped>
.login-page {
    min-height: 100vh;
    width: 100vw;
    display: flex;
    justify-content: center;
    align-items: center;
    position: fixed;
    top: 0;
    left: 0;
    background-color: #000;
}

.login-container {
    width: 100%;
    max-width: 400px;
    padding: 40px 20px;
    background-color: #1c1c1e;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

/* 只保留特定於登入頁面的獨特樣式 */
.logo-container {
    text-align: center;
    margin-bottom: 0%;
}

.logo {
    width: 200px;
    height: auto;
}

.title {
    color: #fff;
    text-align: center;
    font-size: 24px;
    margin-bottom: 32px;
    font-weight: 500;
}

.form-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.input-field {
    padding: 14px 16px;
    border: 1px solid #333;
    border-radius: 8px;
    background-color: #1a1a1a;
    color: #fff;
    font-size: 16px;
    transition: all 0.3s ease;
}

.input-field:focus {
    outline: none;
    border-color: #007bff;
    background-color: #222;
}

.input-field::placeholder {
    color: #666;
}

.remember-me {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #fff;
    font-size: 14px;
}

.login-button {
    width: 100%;
    padding: 14px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: background-color 0.3s ease;
}

.login-button:hover {
    background-color: #0056b3;
}

.links {
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
}

.links a {
    color: #007bff;
    text-decoration: none;
    font-size: 14px;
    transition: color 0.3s ease;
}

.links a:hover {
    color: #0056b3;
    text-decoration: underline;
}
</style>
