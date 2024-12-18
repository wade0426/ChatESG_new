<template>
  <div class="signup-page">
    <div class="signup-container">
        <div class="logo">
            <img src="@/assets/logo_chatesg.png" alt="Logo">
        </div>
        <h1>建立帳號</h1>
        <form @submit.prevent="handleSignup">
            <div class="input-group">
                <select v-model="organization" required>
                    <option value="" disabled selected>選擇組織名稱</option>
                    <option value="國立臺中科技大學">國立臺中科技大學</option>
                    <option value="勤業眾信">勤業眾信</option>
                    <option value="行動貝果">行動貝果</option>
                </select>
            </div>
            <div class="input-group">
                <input type="text" v-model="username" placeholder="使用者名稱" required>
            </div>
            <div class="input-group">
                <input type="email" v-model="email" placeholder="電子郵件" required>
            </div>
            <div class="input-group">
                <input type="password" v-model="password" placeholder="密碼" required>
            </div>
            <div class="input-group">
                <input type="password" v-model="confirmPassword" placeholder="確認密碼" required>
            </div>
            <div class="terms">
                <input type="checkbox" id="terms" v-model="agreeToTerms" required>
                <label for="terms">我同意 <a href="#">服務條款</a> 和 <a href="#">隱私政策</a></label>
            </div>
            <button 
                type="submit" 
                class="button" 
                :disabled="!isFormValid"
                :title="buttonTitle"
            >註冊</button>
        </form>
        <div class="links">
            <router-link to="/login">已經有帳號？登入</router-link>
        </div>
    </div>
  </div>
</template>

<script>
export default {
    name: 'Signup',
    data() {
        return {
            organization: '',
            username: '',
            email: '',
            password: '',
            confirmPassword: '',
            agreeToTerms: false
        }
    },
    computed: {
        isFormValid() {
            return this.organization && 
                   this.username && 
                   this.email && 
                   this.password && 
                   this.password === this.confirmPassword &&
                   this.agreeToTerms
        },
        buttonTitle() {
            if (this.isFormValid) return ''
            
            let message = '請完成以下項目：'
            if (!this.organization) message += '\n- 選擇組織'
            if (!this.username) message += '\n- 輸入使用者名稱'
            if (!this.email) message += '\n- 輸入電子郵件'
            if (!this.password) message += '\n- 輸入密碼'
            if (this.password !== this.confirmPassword) message += '\n- 確認密碼不匹配'
            if (!this.agreeToTerms) message += '\n- 同意服務條款'
            
            return message
        }
    },
    methods: {
        handleSignup() {
            if(!this.isFormValid) return

            // 這裡可以加入註冊邏輯
            console.log('註冊資料:', {
                organization: this.organization,
                username: this.username,
                email: this.email,
                password: this.password
            })
        }
    }
}
</script>

<!-- scoped 用於限制樣式只影響此元件 -->
<style scoped>
.signup-page {
    margin: 0;
    padding: 0;
    min-height: 100vh;
    width: 100vw;
    background-color: #000;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.signup-container {
    background-color: #1c1c1e;
    padding: 40px;
    border-radius: 18px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 2px 20px rgba(255, 255, 255, 0.1);
}

.logo {
    text-align: center;
}

.logo img {
    width: 140px;
    height: 120px;
}

h1 {
    color: #fff;
    text-align: center;
    font-size: 24px;
    margin-bottom: 30px;
}

.input-group {
    margin-bottom: 20px;
}

.input-row {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
}

.input-row .input-group {
    flex: 1;
    margin-bottom: 0;
}

input[type="text"],
input[type="password"],
input[type="email"] {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 8px;
    background-color: #2c2c2e;
    color: #fff;
    font-size: 16px;
    box-sizing: border-box;
}

input::placeholder {
    color: #8e8e93;
}

.button {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 8px;
    background-color: #0a84ff;
    color: #fff;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.button:disabled {
    background-color: #666;
    cursor: not-allowed;
}

.button:hover:not(:disabled) {
    background-color: #007aff;
}

.terms {
    display: flex;
    align-items: flex-start;
    margin: 20px 0;
    color: #8e8e93;
    font-size: 14px;
}

.terms input[type="checkbox"] {
    margin-right: 8px;
    margin-top: 3px;
}

.terms a {
    color: #0a84ff;
    text-decoration: none;
}

.terms a:hover {
    text-decoration: underline;
}

.links {
    text-align: center;
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    width: 100%;
}

.links a {
    color: #0a84ff;
    text-decoration: none;
    font-size: 14px;
    padding: 10px 0;
    width: 100%;
}

select {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 8px;
    background-color: #2c2c2e;
    color: #fff;
    font-size: 16px;
    box-sizing: border-box;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 12px center;
    background-size: 16px;
    cursor: pointer;
}

select:focus {
    outline: none;
}

select option {
    background-color: #2c2c2e;
    color: #fff;
}

.button[disabled] {
    position: relative;
}

.button[disabled]:hover::after {
    content: attr(title);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    padding: 8px;
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    border-radius: 4px;
    font-size: 14px;
    white-space: pre-line;
    margin-bottom: 8px;
    z-index: 1000;
    width: max-content;
    max-width: 300px;
}
</style>