import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
    state: () => ({
        userID: null,
        username: '',
        isAuthenticated: false
    }),

    actions: {
        login(userID, username) {
            this.userID = userID
            this.username = username
            this.isAuthenticated = true

            // 保存到 sessionStorage
            sessionStorage.setItem('userID', userID)
            sessionStorage.setItem('username', username)
        },

        logout() {
            this.userID = null
            this.username = ''
            this.isAuthenticated = false

            // 清除 sessionStorage
            sessionStorage.removeItem('userID')
            sessionStorage.removeItem('username')
        },

        initializeFromStorage() {
            const userID = sessionStorage.getItem('userID')
            const username = sessionStorage.getItem('username')

            if (userID && username) {
                this.login(userID, username)
            }
        }
    }
}) 