<template>
    <div class="header">
        <div class="menu-icon" @click="handleOpenNav">
            <div></div>
            <div></div>
            <div></div>
        </div>
        <div class="search-bar" style="display: none;">
            <div class="search-icon">
                <svg viewBox="0 0 24 24">
                    <path
                        d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
                </svg>
            </div>
            <input 
                type="text" 
                placeholder="搜尋您的內容。"
                v-model="searchQuery"
                @input="handleSearchInput"
            >
        </div>
        <div class="user-profile" @click="toggleDropdown">
            <div class="user-avatar" id="user-avatar"></div>
            <div class="user-info">
                <span class="organization-name" id="organization-name"></span>
                <span class="user-name" id="user-name"></span>
            </div>
            <span class="dropdown-arrow">▼</span>
            <div class="dropdown-menu" id="userDropdown">
                <div class="dropdown-menu-content">
                    <a href="/user_profile"><span>帳號</span></a>
                    <a href="#"><span>管理組織</span></a>
                    <div class="menu-divider"></div>
                    <a href="#"><span>設定</span></a>
                    <a href="#"><span>最新消息</span></a>
                    <a href="#"><span>方案和定價</span></a>
                    <a href="#"><span>隱私權政策</span></a>
                    <div class="menu-divider"></div>
                    <a href="#" @click="logout"><span>登出</span></a>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'

const emit = defineEmits(['openNav'])

const userStore = useUserStore()

// 使用 ref 函式建立可被監聽的變數
const userName = computed(() => userStore.username)
const userAvatarUrl = computed(() => userStore.avatarUrl)
const userOrganizationName = computed(() => userStore.organizationName)

const defaultAvatar = 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png'

// 定義更新界面的函數
const updateUserInterface = () => {
    const userAvatarElement = document.getElementById('user-avatar')
    if (userAvatarElement) {
        userAvatarElement.style.backgroundImage = `url(${userStore.avatarUrl || defaultAvatar})`
    }

    const organizationElement = document.getElementById('organization-name')
    if (organizationElement) {
        organizationElement.textContent = userStore.organizationName
    }

    const userNameElement = document.getElementById('user-name')
    if (userNameElement) {
        userNameElement.textContent = userStore.username
    }
}

// 新增搜索相關的響應式變量
const searchQuery = ref('')

// 監聽搜索輸入
const handleSearchInput = () => {
    console.log('搜索內容:', searchQuery.value)
}

// 監聽搜索內容的變化
watch(searchQuery, (newValue) => {
    console.log('搜索內容更新為:', newValue)
})

const handleOpenNav = () => {
    emit('openNav')
}

const toggleDropdown = () => {
    document.getElementById("userDropdown").classList.toggle("show");
}

const logout = async () => {
    try {
        userStore.logout()  // 調用 Pinia store 的登出方法
        // 重整頁面
        window.location.reload();
    } catch (error) {
        console.error('登出時發生錯誤:', error)
    }
}

// 監聽用戶資料變化並更新界面
watch(
    () => [userStore.username, userStore.avatarUrl, userStore.organizationName],
    () => {
        updateUserInterface()
    },
    { immediate: true }
)

onMounted(() => {
    // 確保用戶資料已加載
    if (userStore.isAuthenticated) {
        userStore.fetchUserProfile()
    }
})
</script>


<style scoped>
.header {
    background-color: #242526;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}

.menu-icon {
    cursor: pointer;
    padding: 10px;
}

.menu-icon div {
    width: 25px;
    height: 3px;
    background-color: white;
    margin: 5px 0;
    border-radius: 3px;
}

.search-bar {
    flex: 1;
    max-width: 600px;
    margin: 0 20px;
    position: relative;
    display: flex;
    align-items: center;
    background-color: #3A3B3C;
    border-radius: 20px;
    padding: 5px 15px;
}

.search-icon {
    width: 24px;
    height: 24px;
    margin-right: 10px;
}

.search-icon svg {
    fill: #B0B3B8;
}

.search-bar input {
    background: none;
    border: none;
    color: white;
    font-size: 15px;
    padding: 5px;
    width: 100%;
}

.search-bar input:focus {
    outline: none;
}

.user-profile {
    display: flex;
    align-items: center;
    cursor: pointer;
    position: relative;
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #3A3B3C;
    margin-right: 10px;
    background-size: cover;
    background-position: center;
}

.user-info {
    text-align: left;
    display: flex;
    flex-direction: column;
    margin-right: 5px;
}

.organization-name {
    color: #E4E6EB;
    font-weight: 600;
    display: block;
    line-height: 1.2;
}

.user-name {
    color: #B0B3B8;
    font-size: 100%;
    display: block;
    line-height: 1.2;
}

.dropdown-arrow {
    margin-left: 5px;
    font-size: 12px;
}

.dropdown-menu {
    display: none;
    position: absolute;
    right: 0;
    top: 100%;
    background-color: #242526;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    margin-top: 5px;
    min-width: 200px;
}

.dropdown-menu.show {
    display: block;
}

.dropdown-menu-content {
    padding: 8px 0;
}

.dropdown-menu a {
    display: block;
    padding: 8px 16px;
    color: white;
    text-decoration: none;
}

.dropdown-menu a:hover {
    background-color: #3A3B3C;
}

.menu-divider {
    height: 1px;
    background-color: #3A3B3C;
    margin: 8px 0;
}
</style> 