<template>
    <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
    <Header @openNav="openNav" />

    <div class="asset-overview">
        <div class="header">
            <h1>資產總覽</h1>
            <div class="search-bar">
                <input type="text" placeholder="搜索資產..." v-model="searchQuery">
            </div>
        </div>

        <div class="asset-table">
            <div v-if="loading" class="loading-state">
                正在加載資產數據...
            </div>
            <div v-else-if="error" class="error-state">
                {{ error }}
                <button @click="fetchAssets" class="retry-button">重試</button>
            </div>
            <table v-else>
                <thead>
                    <tr>
                        <th @click="sort('AssetName')" class="sortable">
                            資產名稱
                            <span class="sort-icon" v-if="sortField === 'AssetName'">
                                {{ sortOrder === 'asc' ? '▲' : '▼' }}
                            </span>
                        </th>
                        <th @click="sort('AssetType')" class="sortable">
                            資產類型
                            <span class="sort-icon" v-if="sortField === 'AssetType'">
                                {{ sortOrder === 'asc' ? '▲' : '▼' }}
                            </span>
                        </th>
                        <th @click="sort('Status')" class="sortable">
                            狀態
                            <span class="sort-icon" v-if="sortField === 'Status'">
                                {{ sortOrder === 'asc' ? '▲' : '▼' }}
                            </span>
                        </th>
                        <th @click="sort('lastUpdated')" class="sortable">
                            最後更新時間
                            <span class="sort-icon" v-if="sortField === 'lastUpdated'">
                                {{ sortOrder === 'asc' ? '▲' : '▼' }}
                            </span>
                        </th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="asset in filteredAndSortedAssets" :key="asset.AssetId" @click="handleRowClick(asset)" style="cursor: pointer;">
                        <td>{{ asset.AssetName }}</td>
                        <td>{{ asset.AssetType }}</td>
                        <td>{{ asset.Status }}</td>
                        <td>{{ asset.lastUpdated }}</td>
                        <td class="actions">
                            <div class="dropdown">
                                <button class="dropdown-toggle" @click="toggleDropdown(asset.AssetId)">
                                    <span class="dots">●●●</span>
                                </button>
                                <div class="dropdown-menu" v-show="activeDropdown === asset.AssetId">
                                    <button @click="openAsset(asset)">開啟</button>
                                    <button @click="renameAsset(asset)">改名</button>
                                    <button @click="deleteAsset(asset)">刪除</button>
                                </div>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- 新增改名對話框 -->
    <div v-if="showRenameModal" class="rename-modal">
        <div class="rename-modal-content">
            <div class="rename-modal-header">
                <h2>重命名資產</h2>
            </div>
            <div class="rename-modal-body">
                <p>請輸入新的資產名稱：</p>
                <input 
                    type="text" 
                    v-model="newAssetName" 
                    placeholder="輸入新名稱"
                    class="rename-input"
                >
            </div>
            <div class="rename-modal-actions">
                <button @click="confirmRename" class="confirm-btn" :disabled="!newAssetName.trim()">確認</button>
                <button @click="cancelRename" class="cancel-btn">取消</button>
            </div>
        </div>
    </div>

    <!-- 新增刪除確認對話框 -->
    <div v-if="showDeleteConfirm" class="delete-confirm-modal">
        <div class="delete-confirm-content">
            <div class="delete-confirm-header">
                <h2>確認刪除</h2>
            </div>
            <div class="delete-confirm-body">
                <p>您確定要刪除這個資產嗎？</p>
            </div>
            <div class="delete-confirm-input">
                <input type="text" v-model="deleteConfirmInput" placeholder="輸入 'Delete' 確認刪除">
            </div>
            <div class="delete-confirm-actions">
                <button @click="confirmDelete" :disabled="deleteConfirmInput !== 'Delete'" class="delete-btn">刪除</button>
                <button @click="cancelDelete" class="cancel-btn">取消</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useToast } from 'vue-toastification'
import { useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import axios from 'axios'

// 初始化 userStore 和 router
const userStore = useUserStore()
const router = useRouter()
const organizationId = computed(() => userStore.organizationID)

// 初始化 toast
const toast = useToast()

const searchQuery = ref('')
const activeDropdown = ref(null)
const sortField = ref('name')
const sortOrder = ref('asc')
const assets = ref([])
const loading = ref(false)
const error = ref(null)
const isSidebarOpen = ref(false)

// 新增刪除相關的響應式變數
const showDeleteConfirm = ref(false)
const deleteConfirmInput = ref('')
const assetToDelete = ref(null)
const isDeleting = ref(false)

// 新增改名相關的響應式變數
const showRenameModal = ref(false)
const newAssetName = ref('')
const assetToRename = ref(null)
const isRenaming = ref(false)

// 獲取資產數據的函數
const fetchAssets = async () => {
    if (!organizationId.value) {
        error.value = '無法獲取組織ID'
        return
    }
    try {
        loading.value = true
        error.value = null
        const response = await axios.get('http://localhost:8000/api/organizations/get_organization_assets', {
            params: {
                organization_id: organizationId.value
            }
        })
        
        if (response.data.status === 'success') {
            console.log(response.data.data)
            assets.value = response.data.data.map(asset => ({
                AssetId: asset.assetID,
                AssetName: asset.assetName,
                AssetType: asset.assetType,
                Status: asset.status,
                lastUpdated: new Date(asset.updatedAt).toLocaleDateString('zh-TW'),
                creator: asset.creator,
                createdAt: asset.createdAt
            }))
        }
    } catch (err) {
        error.value = '獲取資產數據失敗：' + (err.response?.data?.detail || err.message)
        console.error('獲取資產失敗:', err)
    } finally {
        loading.value = false
    }
}

// 監聽 organizationId 的變化
watch(organizationId, (newVal) => {
    if (newVal) {
        fetchAssets()
    }
}, { immediate: true })

const openNav = () => {
    isSidebarOpen.value = true
}

const closeNav = () => {
    isSidebarOpen.value = false
}

const sort = (field) => {
    if (sortField.value === field) {
        sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
        sortField.value = field
        sortOrder.value = 'asc'
    }
}

const sortedAssets = computed(() => {
    return [...assets.value].sort((a, b) => {
        let aValue = a[sortField.value]
        let bValue = b[sortField.value]
        
        if (sortField.value === 'lastUpdated') {
            aValue = new Date(aValue)
            bValue = new Date(bValue)
        }

        if (sortOrder.value === 'asc') {
            return aValue > bValue ? 1 : -1
        } else {
            return aValue < bValue ? 1 : -1
        }
    })
})

const filteredAndSortedAssets = computed(() => {
    const query = searchQuery.value.toLowerCase().trim()
    if (!query) return sortedAssets.value

    return sortedAssets.value.filter(asset => {
        return asset.AssetName.toLowerCase().includes(query) ||
               asset.AssetType.toLowerCase().includes(query) ||
               asset.Status.toLowerCase().includes(query)
    })
})

const toggleDropdown = (assetId) => {
    activeDropdown.value = activeDropdown.value === assetId ? null : assetId
}

const openAsset = (asset) => {
    if (asset.AssetType === 'company_info') {
        router.push(`/company-info-edit?assetId=${asset.AssetId}`)
    }
    else if (asset.AssetType === 'standard_template') {
        router.push(`/create-major-issues-list?assetId=${asset.AssetId}`)
    }
    else if (asset.AssetType === 'report') {
        router.push(`/report-edit?assetId=${asset.AssetId}`)
    }
    else {
        toast.info('此類型資產暫不支持開啟')
    }
    activeDropdown.value = null
}

const renameAsset = (asset) => {
    assetToRename.value = asset
    newAssetName.value = asset.AssetName
    showRenameModal.value = true
    activeDropdown.value = null
}

const confirmRename = async () => {
    if (!newAssetName.value.trim()) {
        return
    }

    try {
        isRenaming.value = true
        const response = await axios.post('http://localhost:8000/api/organizations/update_asset_name', {
            asset_id: assetToRename.value.AssetId,
            organization_id: organizationId.value,
            asset_name: newAssetName.value.trim()
        })

        // 更新本地資產列表中的名稱
        const index = assets.value.findIndex(a => a.AssetId === assetToRename.value.AssetId)
        if (index !== -1) {
            assets.value[index].AssetName = newAssetName.value.trim()
        }

        showRenameModal.value = false
        assetToRename.value = null
        newAssetName.value = ''
        
        // 顯示成功提示
        toast.success('資產名稱已成功更新')
    } catch (err) {
        toast.error('更新資產名稱失敗：' + (err.response?.data?.detail || err.message))
        console.error('更新資產名稱失敗:', err)
    } finally {
        isRenaming.value = false
    }
}

const cancelRename = () => {
    showRenameModal.value = false
    assetToRename.value = null
    newAssetName.value = ''
}

const deleteAsset = async (asset) => {
    assetToDelete.value = asset
    showDeleteConfirm.value = true
    deleteConfirmInput.value = ''
    activeDropdown.value = null
}

const confirmDelete = async () => {
    if (deleteConfirmInput.value !== 'Delete') {
        return
    }

    try {
        isDeleting.value = true
        const response = await axios.post('http://localhost:8000/api/organizations/delete_asset', {
            asset_id: assetToDelete.value.AssetId,
            user_id: userStore.userID,
            organization_id: organizationId.value
        })

        if (response.data.message === '資產已成功刪除') {
            assets.value = assets.value.filter(a => a.AssetId !== assetToDelete.value.AssetId)
            showDeleteConfirm.value = false
            assetToDelete.value = null
            toast.success('資產已成功刪除')
        }
    } catch (err) {
        toast.error('刪除資產失敗：' + (err.response?.data?.detail || err.message))
        console.error('刪除資產失敗:', err)
    } finally {
        isDeleting.value = false
    }
}

const cancelDelete = () => {
    showDeleteConfirm.value = false
    assetToDelete.value = null
    deleteConfirmInput.value = ''
}

const handleRowClick = (asset) => {
    console.log('點擊行的資產ID:', asset.AssetId)
}

// 點擊其他地方關閉下拉菜單
const closeDropdowns = (event) => {
    if (!event.target.closest('.dropdown')) {
        activeDropdown.value = null
    }
}

// 在組件掛載時獲取資產數據
onMounted(() => {
    if (organizationId.value) {
        fetchAssets()
    }
    document.addEventListener('click', closeDropdowns)
})

onUnmounted(() => {
    document.removeEventListener('click', closeDropdowns)
})
</script>

<style scoped>
.asset-overview {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.header h1 {
    color: white;
    font-size: 24px;
}

.search-bar input {
    padding: 8px 16px;
    border-radius: 4px;
    border: 1px solid #3A3B3C;
    background-color: #3A3B3C;
    color: white;
    width: 300px;
}

.asset-table {
    position: relative;
    background-color: #242526;
    border-radius: 8px;
}

table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}

th, td {
    padding: 12px 16px;
    text-align: left;
    color: white;
    border-bottom: 1px solid #3A3B3C;
}

th {
    background-color: #2C2D2E;
    font-weight: normal;
    color: #999;
    font-size: 14px;
}

tr {
    background-color: #1E1F20;
}

tr:hover {
    background-color: #2C2D2E;
}

.actions {
    position: relative;
    width: 60px;
    text-align: center;
}

.dropdown {
    position: relative;
    display: inline-block;
}

.dropdown-toggle {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    padding: 8px;
    font-size: 20px;
    font-weight: bold;
    line-height: 1;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.dropdown-toggle:hover {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

.dots {
    font-size: 20px;
    line-height: 1;
    letter-spacing: 2px;
}

.dropdown-menu {
    position: absolute;
    right: 0;
    top: calc(100% - 8px);
    background-color: #2C2D2E;
    border: 1px solid #3A3B3C;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    min-width: 120px;
    z-index: 1000;
}

tr:last-child .dropdown-menu {
    bottom: calc(100% - 8px);
    top: auto;
}

.dropdown-menu button {
    display: block;
    width: 100%;
    padding: 10px 16px;
    text-align: left;
    background: none;
    border: none;
    color: #E4E6EB;
    cursor: pointer;
    font-size: 14px;
    transition: background-color 0.2s;
    white-space: nowrap;
}

.dropdown-menu button:hover {
    background-color: #3A3B3C;
}

.dropdown-menu button:not(:last-child) {
    border-bottom: 1px solid #3A3B3C;
}

/* 移除原有的編輯和刪除按鈕樣式 */
.table-actions .edit-btn, 
.table-actions .delete-btn {
    display: none;
}

.sortable {
    cursor: pointer;
    user-select: none;
    position: relative;
}

.sortable:hover {
    background-color: #3A3B3C;
}

.sort-icon {
    margin-left: 5px;
    font-size: 12px;
}

.loading-state, .error-state {
    padding: 20px;
    text-align: center;
    color: #E4E6EB;
}

.error-state {
    color: #ff6b6b;
}

.retry-button {
    margin-top: 10px;
    padding: 8px 16px;
    background-color: #3A3B3C;
    border: none;
    border-radius: 4px;
    color: white;
    cursor: pointer;
}

.retry-button:hover {
    background-color: #4A4B4C;
}

/* 新增刪除確認對話框的樣式 */
.delete-confirm-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.delete-confirm-content {
    background-color: #242526;
    padding: 24px;
    border-radius: 8px;
    width: 400px;
    max-width: 90%;
}

.delete-confirm-header {
    margin-bottom: 16px;
}

.delete-confirm-header h2 {
    color: #E4E6EB;
    font-size: 20px;
    margin: 0;
}

.delete-confirm-body {
    margin-bottom: 20px;
}

.delete-confirm-body p {
    color: #B0B3B8;
    margin-bottom: 16px;
}

.delete-confirm-input {
    width: 100%;
    padding: 8px;
    background-color: #3A3B3C;
    border: 1px solid #4A4B4C;
    border-radius: 4px;
    color: white;
    margin-bottom: 16px;
}

.delete-confirm-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

.delete-confirm-actions button {
    padding: 8px 16px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
}

.delete-confirm-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.cancel-btn {
    background-color: #3A3B3C;
    color: #E4E6EB;
}

.delete-btn {
    background-color: #BE4040;
    color: white;
}

.cancel-btn:hover {
    background-color: #4A4B4C;
}

.delete-btn:hover:not(:disabled) {
    background-color: #A03030;
}

/* 新增改名模態框樣式 */
.rename-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.rename-modal-content {
    background-color: #242526;
    padding: 24px;
    border-radius: 8px;
    width: 400px;
    max-width: 90%;
}

.rename-modal-header {
    margin-bottom: 16px;
}

.rename-modal-header h2 {
    color: #E4E6EB;
    font-size: 20px;
    margin: 0;
}

.rename-modal-body {
    margin-bottom: 20px;
}

.rename-modal-body p {
    color: #B0B3B8;
    margin-bottom: 16px;
}

.rename-input {
    width: 100%;
    padding: 8px;
    background-color: #3A3B3C;
    border: 1px solid #4A4B4C;
    border-radius: 4px;
    color: white;
    margin-bottom: 16px;
}

.rename-modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

.rename-modal-actions button {
    padding: 8px 16px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
}

.rename-modal-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.confirm-btn {
    background-color: #0084FF;
    color: white;
}

.confirm-btn:hover:not(:disabled) {
    background-color: #0073E6;
}
</style> 