// 引入 Pinia 的 defineStore 函數
import { defineStore } from 'pinia'

// 定義一個名為 'user' 的 store
export const useUserStore = defineStore('user', {
    // 定義狀態
    state: () => ({
        userID: null, // 用戶ID，初始為 null
        username: '', // 用戶名，初始為空字符串
        isAuthenticated: false // 認證狀態，初始為 false
    }),

    // 定義行為
    actions: {
        // 登入方法
        login(userID, username) {
            this.userID = userID // 設置用戶ID
            this.username = username // 設置用戶名
            this.isAuthenticated = true // 設置認證狀態為 true

            // 保存用戶訊息到 sessionStorage
            sessionStorage.setItem('userID', userID)
            sessionStorage.setItem('username', username)
        },

        // 登出方法
        logout() {
            this.userID = null // 清除用戶ID
            this.username = '' // 清除用戶名
            this.isAuthenticated = false // 設置認證狀態為 false

            // 清除 sessionStorage 中的用戶訊息
            sessionStorage.removeItem('userID')
            sessionStorage.removeItem('username')
        },

        // 從 sessionStorage 初始化用戶訊息
        initializeFromStorage() {
            const userID = sessionStorage.getItem('userID') // 獲取用戶ID
            const username = sessionStorage.getItem('username') // 獲取用戶名

            // 如果用戶ID和用戶名存在，則執行登入
            if (userID && username) {
                this.login(userID, username)
            }
        }
    }
})