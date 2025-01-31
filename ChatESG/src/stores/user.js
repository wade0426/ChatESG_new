// 引入 Pinia 的 defineStore 函數
import { defineStore } from 'pinia'

// 定義一個名為 'user' 的 store
export const useUserStore = defineStore('user', {
    // 定義狀態
    state: () => ({
        userID: null,
        username: '',
        isAuthenticated: false,
        organizationName: '',
        email: '',
        avatarUrl: '',
        organizationRoles: []
    }),

    // 定義行為
    actions: {
        // 登入方法
        login(userID, username, access_token) {
            this.userID = userID
            this.username = username
            this.isAuthenticated = true

            // 保存用戶訊息到 sessionStorage
            sessionStorage.setItem('userID', userID)
            sessionStorage.setItem('username', username)
            sessionStorage.setItem('access_token', access_token)
        },

        // 登出方法
        logout() {
            this.userID = null
            this.username = ''
            this.isAuthenticated = false
            this.organizationName = ''
            this.email = ''
            this.avatarUrl = ''
            this.organizationRoles = []

            // 清除 sessionStorage 中的用戶訊息
            sessionStorage.removeItem('userID')
            sessionStorage.removeItem('username')
            sessionStorage.removeItem('access_token')
        },

        // 從 sessionStorage 初始化用戶訊息
        async initializeFromStorage() {
            const userID = sessionStorage.getItem('userID')
            const username = sessionStorage.getItem('username')
            const access_token = sessionStorage.getItem('access_token')

            if (userID && username && access_token) {
                this.login(userID, username, access_token)
                await this.fetchUserProfile()  // 添加 await 等待获取完整用户资料
            }
        },

        // 更新用戶資料
        async fetchUserProfile(retryCount = 3) {
            try {
                const response = await fetch('http://localhost:8000/api/user/profile/Personal_Information', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: this.userID
                    })
                })

                if (!response.ok) {
                    console.error('API請求失敗:', response.status, response.statusText)
                    const errorText = await response.text()
                    console.error('錯誤詳情:', errorText)
                    
                    // 如果還有重試次數，則等待後重試
                    if (retryCount > 0) {
                        console.log(`重試獲取用戶資料，剩餘重試次數: ${retryCount - 1}`)
                        await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒後重試
                        return this.fetchUserProfile(retryCount - 1)
                    }
                    return
                }

                const data = await response.json()
                console.log('從API獲取的資料:', data)
                if (data.status === 'success') {
                    this.updateUserInfo(data.data)
                }
            } catch (error) {
                console.error('獲取用戶資料失敗:', error)
                if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                    console.error('無法連接到後端服務器，請確保服務器正在運行')
                }
                
                // 如果還有重試次數，則等待後重試
                if (retryCount > 0) {
                    console.log(`重試獲取用戶資料，剩餘重試次數: ${retryCount - 1}`)
                    await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒後重試
                    return this.fetchUserProfile(retryCount - 1)
                }
            }
        },

        // 更新用戶信息
        updateUserInfo(data) {
            this.username = data.userName || this.username
            this.email = data.email || this.email
            this.avatarUrl = data.avatarUrl || this.avatarUrl
            this.organizationName = data.organizationName || this.organizationName
            this.organizationRoles = data.organizationRoles || this.organizationRoles
        },

        // 更新用戶名
        async updateUsername(newUsername) {
            try {
                const response = await fetch('http://localhost:8000/api/user/profile/Change_Username', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: this.userID,
                        new_username: newUsername
                    })
                })
                const data = await response.json()
                if (data.status === 'success') {
                    this.username = newUsername
                    return { success: true }
                }
                return { success: false, error: data.detail }
            } catch (error) {
                return { success: false, error: '發生錯誤，請稍後再試' }
            }
        },

        // 更新密碼
        async updatePassword(currentPassword, newPassword) {
            try {
                const response = await fetch('http://localhost:8000/api/user/profile/Change_Password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: this.userID,
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                })
                const data = await response.json()
                return {
                    success: data.status === 'success',
                    error: data.status === 'success' ? null : (data.detail || '密碼修改失敗')
                }
            } catch (error) {
                return { success: false, error: '發生錯誤，請稍後再試' }
            }
        }
    }
})