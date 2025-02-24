<template>
  <div class="signup-page">
    <div class="signup-container">
        <div class="logo">
            <img src="@/assets/logo_chatesg.png" alt="Logo">
        </div>
        <h1>建立帳號</h1>
        <form @submit.prevent="handleSignup">
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
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

export default {
    name: 'Signup',
    data() {
        return {
            username: '',
            email: '',
            password: '',
            confirmPassword: '',
            agreeToTerms: false
        }
    },
    computed: {
        isFormValid() {
            return this.username && 
                   this.email && 
                   this.password && 
                   this.password === this.confirmPassword &&
                   this.agreeToTerms
        },
        buttonTitle() {
            if (this.isFormValid) return ''
            
            let message = '請完成以下項目：'
            if (!this.username) message += '\n- 輸入使用者名稱'
            if (!this.email) message += '\n- 輸入電子郵件'
            if (!this.password) message += '\n- 輸入密碼'
            if (this.password !== this.confirmPassword) message += '\n- 確認密碼不匹配'
            if (!this.agreeToTerms) message += '\n- 同意服務條款'
            
            return message
        }
    },
    methods: {
        async handleSignup() {
            if(!this.isFormValid) return

            try {
                const response = await fetch(`${configStore.apiBaseUrl}/api/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        username: this.username,
                        userEmail: this.email,
                        password: this.password
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || `註冊失敗：${response.status}`);
                }

                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('註冊成功！');
                    this.$router.push('/login');
                } else {
                    alert(data.detail || '註冊失敗，請稍後再試');
                }
            } catch (error) {
                console.error('註冊錯誤:', error);
                alert(error.message || '註冊時發生錯誤，請稍後再試');
            }
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
    background-color: #000;
}

.signup-container {
    width: 100%;
    max-width: 400px;
    padding: 40px;
    background-color: #1c1c1e;
    border-radius: 18px;
    box-shadow: 0 2px 20px rgba(255, 255, 255, 0.1);
}

.logo {
    text-align: center;
    margin-bottom: 20px;
}

.logo img {
    width: 140px;
    height: 120px;
}

.input-group {
    margin-bottom: 20px;
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