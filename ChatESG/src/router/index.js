import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/home',
            name: 'Home',
            component: () => import('../components/home.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/login',
            name: 'Login',
            component: () => import('../components/login.vue'),
            meta: { requiresAuth: false }
        },
        {
            path: '/signup',
            name: 'Signup',
            component: () => import('../components/signup.vue'),
            meta: { requiresAuth: false }
        },
        {
            path: '/company-info-edit',
            name: 'CompanyInfoEdit',
            component: () => import('../components/CompanyInfoEdit.vue'),
            meta: { requiresAuth: true }
        }
    ]
})

// 在每次路由變更前執行
router.beforeEach((to, from, next) => {
    // 從 localStorage 中獲取用戶認證信息
    const isAuthenticated = localStorage.getItem('user')

    // 如果目標路由需要認證且用戶未認證，則重定向到登入頁面
    if (to.meta.requiresAuth && !isAuthenticated) {
        next('/login')
    } else {
        // 否則允許路由變更
        next()
    }
})

export default router 