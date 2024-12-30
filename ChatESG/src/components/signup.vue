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
    min-height: 100vh;
    width: 100vw;
    display: flex;
    justify-content: center;
    align-items: center;
}

.signup-container {
    composes: container;  /* 使用全局容器樣式 */
}

/* 只保留特定於註冊頁面的獨特樣式 */
.logo {
    width: 140px;
    height: 120px;
}

/* ... 其他特定樣式 ... */
</style>