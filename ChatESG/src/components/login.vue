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
export default {

  name: 'Login',
  data() { // 定義元件的資料
    return {
      username: '',
      password: '',
      rememberMe: false,
      userID: null,
    }
  },

  // mounted 生命週期鉤子 (DOM後立即執行)
  mounted() {
    this.init();
  },

  methods: {
    handleLogin() { //事件觸發
      // 模擬與資料庫的API請求
      const mockApiCall = () => {
        return new Promise((resolve, reject) => {
          // 假設正確的帳號密碼
          if(this.username === 'admin' && this.password === '1') {
            resolve({
              status: 'success',
              userID: 'user_123'
            });
          } else {
            reject({
              status: 'error',
              message: '帳號或密碼錯誤'
            });
          }
        });
      }

      // 執行登入
      mockApiCall()
        .then(response => {
          this.userID = response.userID;
          this.showToast('登入成功!', true);
          // 設定 sessionStorage
          sessionStorage.setItem('userID', this.userID);
          // 如果勾選記住我,可以將資訊存入localStorage
          if(this.rememberMe) {
            // 存 username 讓使用者登出時可以更快登入
            localStorage.setItem('username', this.username);
          }
          // 路由導航到首頁
          this.$router.push('/home');
        })
        .catch(error => {
          // 顯示錯誤訊息
          this.showToast(error.message, false);
          this.password = ''; // 清空密碼
        });
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
      this.username = localStorage.getItem('username') || '';
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
