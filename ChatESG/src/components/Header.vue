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
        <div class="user-profile" @click="isDropdownVisible = !isDropdownVisible">
            <div class="user-avatar" :style="avatarStyle"></div>
            <div class="user-info">
                <span class="organization-name">{{ userOrganizationName }}</span>
                <span class="user-name">{{ userName }}</span>
            </div>
            <span class="dropdown-arrow">▼</span>
            <Transition name="fade">
                <div v-show="isDropdownVisible" class="dropdown-menu">
                    <div class="dropdown-menu-content">
                        <RouterLink to="/user-profile"><span>帳號</span></RouterLink>
                        <RouterLink to="/organization/details"><span>管理組織</span></RouterLink>
                        <div class="menu-divider"></div>
                        <RouterLink to="/settings"><span>設定</span></RouterLink>
                        <RouterLink to="/news"><span>最新消息</span></RouterLink>
                        <RouterLink to="/pricing"><span>方案和定價</span></RouterLink>
                        <RouterLink to="/privacy"><span>隱私權政策</span></RouterLink>
                        <div class="menu-divider"></div>
                        <a href="#" @click.prevent="logout"><span>登出</span></a>
                    </div>
                </div>
            </Transition>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRoute, RouterLink } from 'vue-router'

// 定義 emit 事件
const emit = defineEmits(['openNav'])

// 使用 userStore 來管理用戶資料
const userStore = useUserStore()

// 使用 route 來獲取當前路由
const route = useRoute()

const isDropdownVisible = ref(false)
const searchQuery = ref('')

const defaultAvatar = 'https://raw.githubusercontent.com/wade0426/ChatESG_new/refs/heads/main/userPhoto/user-icons.png'

// 計算屬性，用於獲取用戶名稱
const userName = computed(() => userStore.username)

// 計算屬性，用於獲取用戶所屬組織名稱
const userOrganizationName = computed(() => userStore.organizationName)

// 計算屬性，用於設置用戶頭像的背景樣式，若無頭像則使用預設頭像
const avatarStyle = computed(() => ({
    backgroundImage: `url(${userStore.avatarUrl || defaultAvatar})`
}))

// 方法
const handleOpenNav = () => emit('openNav')

const handleSearchInput = () => {
    console.log('搜索內容:', searchQuery.value)
}

const logout = async () => {
    try {
        await userStore.logout()
        window.location.reload()
    } catch (error) {
        console.error('登出時發生錯誤:', error)
    }
}

// 點擊外部關閉下拉選單
const handleClickOutside = (event) => {
    const userProfile = event.target.closest('.user-profile')
    if (!userProfile && isDropdownVisible.value) {
        isDropdownVisible.value = false
    }
}

// 初始化函數
const initializeUser = async () => {
    if (!userStore.isAuthenticated) {
        await userStore.initializeFromStorage()
        if (!userStore.isAuthenticated && route.path !== '/login' && route.path !== '/signup') {
            window.location.href = '/login'
            return
        }
    }
    await userStore.fetchUserProfile()
}

// 生命週期鉤子
onMounted(async () => {
    await initializeUser()
    document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
})

// 監聽路由變化
watch(
    () => route.fullPath,
    async (newPath, oldPath) => {
        // 只在路由實際發生變化且不是首次加載時才調用
        if (newPath !== oldPath && oldPath !== undefined) {
            await initializeUser()
        }
    }
)
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
    transition: transform 0.2s ease;
}

.user-profile:hover .user-avatar {
    transform: scale(1.05);
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
    position: absolute;
    right: 0;
    top: 100%;
    background-color: #242526;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    margin-top: 5px;
    min-width: 200px;
    transform-origin: top right;
    transition: all 0.3s ease;
}

.dropdown-menu-content {
    padding: 8px 0;
}

.dropdown-menu a {
    display: block;
    padding: 8px 16px;
    color: white;
    text-decoration: none;
    transition: background-color 0.2s ease;
}

.dropdown-menu a:hover {
    background-color: #3A3B3C;
}

.menu-divider {
    height: 1px;
    background-color: #3A3B3C;
    margin: 8px 0;
}

/* 添加过渡动画 */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(-10px);
}
</style> 