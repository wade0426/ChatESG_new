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
        },
        {
            path: '/found-organization',
            name: 'FoundOrganization',
            component: () => import('../components/found_organization.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/user-profile',
            name: 'UserProfile',
            component: () => import('../components/UserProfile.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/organization',
            component: () => import('../components/OrganizationLayout.vue'),
            meta: { requiresAuth: true },
            children: [
                {
                    path: 'details',
                    name: 'OrganizationDetails',
                    component: () => import('../components/OrganizationDashboard.vue')
                },
                {
                    path: 'members',
                    name: 'OrganizationMembers',
                    component: () => import('../components/OrganizationMember.vue')
                },
                {
                    path: 'roles',
                    name: 'OrganizationRoles',
                    component: () => import('../components/OrganizationRole.vue')
                },
                {
                    path: 'permissions',
                    name: 'OrganizationPermissions',
                    component: () => import('../components/OrganizationPermission.vue')
                },
                {
                    path: 'payment',
                    name: 'PaymentAndPlan',
                    component: () => import('../components/PaymentAndPlan.vue')
                },
                {
                    path: 'purchases',
                    name: 'PurchaseRecord',
                    component: () => import('../components/PurchaseRecord.vue')
                },
                {
                    path: 'membership-application-review',
                    name: 'MembershipApplicationReview',
                    component: () => import('../components/MembershipApplicationReview.vue')
                },
                {
                    path: 'report-management',
                    name: 'ReportManagement',
                    component: () => import('../components/ReportManagement.vue')
                },
                {
                    path: 'audit-log',
                    name: 'AuditLog',
                    component: () => import('../components/AuditLog.vue')
                }
            ]
        },
        {
            path: '/create-major-issues-list',
            name: 'CreateMajorIssuesList',
            component: () => import('../components/CreateMajorIssuesList.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/asset-overview',
            name: 'AssetOverview',
            component: () => import('../components/AssetOverview.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/report-edit',
            name: 'ReportEdit',
            component: () => import('../components/ReportEdit.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/review-list',
            name: 'ReviewList',
            component: () => import('@/components/ReviewList.vue'),
            meta: {
                requiresAuth: true,
                title: '審核列表'
            }
        },
        {
            path: '/review',
            name: 'ReviewDetail',
            component: () => import('@/components/ReviewDetail.vue'),
            meta: {
                requiresAuth: true,
                title: '審核詳情'
            }
        }
    ]
})

// 在每次路由變更前執行
router.beforeEach((to, from, next) => {
    // 從 sessionStorage 中獲取用戶認證訊息
    const isAuthenticated = sessionStorage.getItem('access_token')

    // 如果目標路由需要認證且用戶未認證，則重定向到登入頁面
    if (to.meta.requiresAuth && !isAuthenticated) {
        next('/login')
    } else {
        // 否則允許路由變更
        next()
    }
})

export default router 