// 引入 Pinia 的 defineStore 函數
import { defineStore } from 'pinia'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/config'
const configStore = useConfigStore()


// 定義一個名為 'organization' 的 store
export const organizationStore = defineStore('organization', {
    state: () => ({
        organizationName: '', // 組織名稱
        organizationId: '', // 組織ID
        organizationCode: '', // 組織加入代碼
        organizationOwner: '', // 組織擁有者
        memberCount: 0, // 組織成員數量
        reportCount: 0, // 組織報告書數量
        roleCount: 0, // 組織身份組數量
        createdAt: '', // 創建時間
        updatedAt: '', // 最後更新時間
        roles: [], // 組織身份組
        members: {}, // 組織成員列表
        description: '', // 組織描述
        avatarUrl: '' // 組織頭像
    }),

    actions: {
        // 初始化組織資訊
        async initializeOrganization() {
            const router = useRouter()
            try {
                // 從 sessionStorage 獲取用戶ID
                const userID = sessionStorage.getItem('userID')
                if (!userID) {
                    console.error('未找到用戶ID')
                    router.push('/login')
                    return false
                }

                // 先獲取用戶的組織訊息
                const orgInfo = await this.getOrganizationByUserId()
                if (!orgInfo || !orgInfo.organization_id) {
                    console.error('未找到組織訊息')
                    router.push('/home')
                    return false
                }

                // 獲取組織詳細訊息
                const success = await this.fetchOrganizationInfo(orgInfo.organization_id)
                if (!success) {
                    console.error('獲取組織資訊失敗')
                    router.push('/home')
                    return false
                }

                return true
            } catch (error) {
                console.error('加載組織資訊時發生錯誤:', error)
                router.push('/home')
                return false
            }
        },

        // 獲取組織資料
        async fetchOrganizationInfo(organizationId) {
            try {
                const response = await axios.post(`${configStore.apiBaseUrl}/api/organizations/info`, {
                    organization_id: organizationId
                })

                if (response.data.status === 'success') {
                    const data = response.data.data
                    console.log('Info_API：',data)
                    this.setOrganizationInfo({
                        orgID: data.id,
                        code: data.code,
                        name: data.name,
                        email: data.email,
                        owner: data.owner.name,
                        description: data.description,
                        avatarUrl: data.avatarUrl,
                        createdAt: data.createdAt,
                        updatedAt: data.updatedAt
                    })

                    this.updateMemberCount(data.memberCount)
                    this.updateReportCount(data.reportCount)
                    this.updateRoles(data.roles)
                    this.updateMembers(data.members)
                    this.updateRoleCount()

                    return true
                }
                return false
            } catch (error) {
                console.error('獲取組織資料失敗:', error)
                return false
            }
        },

        // 設置組織基本資訊
        setOrganizationInfo(info) {
            this.organizationName = info.name
            this.organizationCode = info.code
            this.organizationId = info.orgID
            this.organizationOwner = info.owner
            this.description = info.description
            this.avatarUrl = info.avatarUrl
            this.createdAt = info.createdAt
            this.updatedAt = info.updatedAt
        },

        // 更新成員數量
        updateMemberCount(count) {
            this.memberCount = count
        },

        // 更新報告書數量 
        updateReportCount(count) {
            this.reportCount = count
        },

        // 更新身份組數量
        updateRoleCount() {
            this.roleCount = this.roles.length
        },

        // 更新組織成員列表
        updateMembers(members) {
            this.members = members
        },

        // 更新組織身份組
        updateRoles(roles) {
            this.roles = roles
        },

        // 通過用戶ID獲取組織訊息
        async getOrganizationByUserId() {
            try {
                const userID = sessionStorage.getItem('userID')
                if (!userID) {
                    console.error('未找到用戶ID')
                    return null
                }

                const response = await axios.post(`${configStore.apiBaseUrl}/api/organizations/get_by_user`, {
                    user_id: userID
                })

                if (response.data.status === 'success') {
                    return response.data.data
                }
                return null
            } catch (error) {
                console.error('通過用戶ID獲取組織訊息失敗:', error)
                return null
            }
        }
    }
})