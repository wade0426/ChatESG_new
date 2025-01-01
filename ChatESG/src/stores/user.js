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
        organizationRole: '一般用戶'
    }),

    // 定義行為
    actions: {
        // 登入方法
        login(userID, username) {
            this.userID = userID
            this.username = username
            this.isAuthenticated = true

            // 保存用戶訊息到 sessionStorage
            sessionStorage.setItem('userID', userID)
            sessionStorage.setItem('username', username)
        },

        // 登出方法
        logout() {
            this.userID = null
            this.username = ''
            this.isAuthenticated = false
            this.organizationName = ''
            this.email = ''
            this.avatarUrl = ''
            this.organizationRole = '一般用戶'

            // 清除 sessionStorage 中的用戶訊息
            sessionStorage.removeItem('userID')
            sessionStorage.removeItem('username')
        },

        // 從 sessionStorage 初始化用戶訊息
        initializeFromStorage() {
            const userID = sessionStorage.getItem('userID')
            const username = sessionStorage.getItem('username')

            if (userID && username) {
                this.login(userID, username)
                this.fetchUserProfile()  // 獲取完整的用戶資料
            }
        },

        // 更新用戶資料
        async fetchUserProfile() {
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
                const data = await response.json()
                if (data.status === 'success') {
                    this.updateUserInfo(data.data)
                }
            } catch (error) {
                console.error('獲取用戶資料失敗:', error)
            }
        },

        // 更新用戶信息
        updateUserInfo(data) {
            this.username = data.userName || this.username
            this.email = data.email || this.email
            this.avatarUrl = data.avatarUrl || this.avatarUrl
            this.organizationName = data.organizationName || this.organizationName
            this.organizationRole = data.organizationRole || this.organizationRole
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