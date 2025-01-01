<template>
  <div class="organization-layout">
    <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
    <Header @openNav="openNav" />
    <div class="content-wrapper">
      <OrganizationSidebar class="org-sidebar" />
      <div class="main-content">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import OrganizationSidebar from './OrganizationSidebar.vue'
import { useUserStore } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'OrganizationLayout',
  components: {
    Sidebar,
    Header,
    OrganizationSidebar
  },
  setup() {
    const isSidebarOpen = ref(false)
    const userStore = useUserStore()
    const router = useRouter()
    const route = useRoute()

    const initializeUser = async () => {
      if (!userStore.isAuthenticated) {
        userStore.initializeFromStorage()
        if (!userStore.isAuthenticated) {
          router.push('/login')
          return
        }
      }
      await userStore.fetchUserProfile()
    }

    // 在組件掛載時初始化
    onMounted(async () => {
      await initializeUser()
    })

    // 監聽路由變化
    watch(
      () => route.fullPath,
      async () => {
        await initializeUser()
      }
    )

    // 使用 computed 屬性來獲取用戶信息
    const userInfo = computed(() => ({
      userName: userStore.username,
      userID: userStore.userID,
      avatarUrl: userStore.avatarUrl,
      email: userStore.email,
      organizationName: userStore.organizationName,
      organizationRole: userStore.organizationRole
    }))

    const openNav = () => {
      isSidebarOpen.value = true
    }

    const closeNav = () => {
      isSidebarOpen.value = false
    }

    return {
      isSidebarOpen,
      openNav,
      closeNav
    }
  }
}
</script>

<style scoped>
.organization-layout {
  min-height: 100vh;
  background-color: #18191A;
  /* background-color: #2c2c2c; */
}

.content-wrapper {
  display: flex;
  /* padding-top: 60px; 為 Header 預留空間 */
  min-height: calc(100vh - 60px);
}

.org-sidebar {
  flex-shrink: 0;
}

.main-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  color: white;
}
</style> 