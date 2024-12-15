<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo-container">
        <img src="@/assets/logo.svg" alt="Logo" class="logo">
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
          <a href="#" class="create-account">建立新帳號</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      rememberMe: false
    }
  },
  methods: {
    handleLogin() {
      // 處理登入邏輯
      console.log('登入資料:', {
        username: this.username,
        password: this.password,
        rememberMe: this.rememberMe
      })
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100vw;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  position: fixed;
  top: 0;
  left: 0;
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 40px 20px;
  background-color: #111;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.logo-container {
  text-align: center;
  margin-bottom: 24px;
}

.logo {
  width: 60px;
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

