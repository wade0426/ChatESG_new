<template>
    <div class="report-management">
      <div class="page-header">
        <h1>報告書管理</h1>
      </div>
      
      <!-- 錯誤提示 -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- 載入中提示 -->
      <div v-if="loading" class="loading-message">
        載入中...
      </div>

      <div class="report-list">
        <div class="table-container">
          <table class="report-table">
            <thead>
              <tr>
                <th>報告書名稱</th>
                <th>建立時間</th>
                <th>更新時間</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in reports" 
                  :key="report.assetID"
                  @contextmenu.prevent="showContextMenu($event, report)"
                  :class="{ 'row-hover': true }">
                <td>{{ report.assetName }}</td>
                <td>{{ formatDate(report.createdAt) }}</td>
                <td>{{ formatDate(report.updatedAt) }}</td>
                <td>
                  <span :class="['status-badge', getStatusClass(report.status)]">
                    {{ getStatusText(report.status) }}
                  </span>
                </td>
                <td>
                  <div class="dropdown">
                    <button class="dropdown-toggle" @click="toggleDropdown(report.assetID, $event)">
                      <span class="dots">●●●</span>
                    </button>
                    <div class="dropdown-menu" v-show="activeDropdown === report.assetID">
                      <button @click="openWorkflowSettings(report)">
                        <i class="fas fa-cog"></i> 設定審核流程
                      </button>
                      <button @click="editReport(report)">
                        <i class="fas fa-edit"></i> 查看審核狀態
                      </button>
                      <button @click="editReport(report)">
                        <i class="fas fa-edit"></i> 編輯報告書
                      </button>
                      <!-- <button @click="downloadReport(report)">
                        <i class="fas fa-download"></i> 下載報告書
                      </button>
                      <button class="delete" @click="confirmDelete(report)">
                        <i class="fas fa-trash"></i> 刪除報告書
                      </button> -->
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 右鍵選單 -->
      <div v-if="showMenu" 
           class="context-menu"
           :style="{ top: menuY + 'px', left: menuX + 'px' }">
        <div class="menu-item" @click="openWorkflowSettings(selectedReport)">
          <i class="fas fa-cog"></i> 設定審核流程
        </div>
        <div class="menu-item" @click="editReport(selectedReport)">
          <i class="fas fa-edit"></i> 編輯報告書
        </div>
        <div class="menu-item" @click="downloadReport(selectedReport)">
          <i class="fas fa-download"></i> 下載報告書
        </div>
        <div class="menu-item delete" @click="confirmDelete(selectedReport)">
          <i class="fas fa-trash"></i> 刪除報告書
        </div>
      </div>

      <!-- 確認刪除對話框 -->
      <div v-if="showDeleteConfirm" class="modal-overlay">
        <div class="modal-content">
          <h3>確認刪除</h3>
          <p>確定要刪除報告書 "{{ selectedReport?.assetName }}" 嗎？</p>
          <div class="modal-actions">
            <button class="btn cancel" @click="showDeleteConfirm = false">取消</button>
            <button class="btn delete" @click="deleteReport">確認刪除</button>
          </div>
        </div>
      </div>

      <!-- 審核流程設定 Modal -->
      <WorkflowSettingsModal 
        ref="workflowSettingsModal"
        :report="selectedReport"
      />
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  import { useUserStore } from '@/stores/user';
  import WorkflowSettingsModal from './WorkflowSettingsModal.vue';
  import { useToast } from 'vue-toastification';
  import { useConfigStore } from '@/stores/config'

  const configStore = useConfigStore()
  
  export default {
    name: 'ReportManagement',
    components: {
      WorkflowSettingsModal
    },
    data() {
      return {
        reports: [],
        showMenu: false,
        menuX: 0,
        menuY: 0,
        selectedReport: null,
        showDeleteConfirm: false,
        activeDropdown: null,
        loading: false,
        error: null,
      };
    },
    async created() {
      // 點擊其他地方時關閉右鍵選單和下拉選單
      document.addEventListener('click', this.closeContextMenu);
      document.addEventListener('click', this.closeDropdown);
      
      // 等待 store 初始化後再獲取報告書
      await this.initializeData();
    },
    beforeUnmount() {
      document.removeEventListener('click', this.closeContextMenu);
      document.removeEventListener('click', this.closeDropdown);
    },
    methods: {
      async initializeData() {
        try {
          this.loading = true;
          const userStore = useUserStore();
          
          // 等待 store 初始化完成，最多等待 3 秒
          let attempts = 0;
          const maxAttempts = 30; // 30 次 * 100ms = 3 秒
          
          while (!userStore.organizationID && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 100)); // 等待 100ms
            attempts++;
          }
          
          if (!userStore.organizationID) {
            throw new Error('無法獲取組織 ID，請確認是否已登入');
          }
          
          await this.fetchReports();
        } catch (error) {
          console.error('初始化數據失敗:', error);
          this.error = error.message || '載入數據失敗，請重新整理頁面';
        } finally {
          this.loading = false;
        }
      },
      async fetchReports() {
        try {
          const response = await axios.post(`${configStore.apiBaseUrl}/api/report/get_report_info`, {
            organizationID: useUserStore().organizationID
          });
          
          if (response.data.status === 'success') {
            this.reports = response.data.data;
          } else {
            throw new Error(response.data.message || '獲取報告書失敗');
          }
        } catch (error) {
          console.error('獲取報告書錯誤:', error);
          this.error = error.message || '獲取報告書失敗';
        }
      },
      formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-TW');
      },
      getStatusText(status) {
        const statusMap = {
          'draft': '草稿',
          'pending': '審核中',
          'approved': '已通過',
          'rejected': '已拒絕'
        };
        return statusMap[status] || status;
      },
      getStatusClass(status) {
        return `status-${status}`;
      },
      openWorkflowSettings(report) {
        try {
          // console.log('Opening workflow settings with report:', report);
          
          if (!report || !report.assetID) {
            console.error('報告書資訊不完整:', report);
            const toast = useToast()
            toast.error('無法開啟審核流程設定：報告書資訊不完整')
            return
          }

          // 先設置 selectedReport
          this.selectedReport = report;
          // console.log('selectedReport set to:', this.selectedReport);

          // 確保 ref 存在且有 showModal 方法
          if (this.$refs.workflowSettingsModal?.showModal) {
            // 等待下一個 tick，確保 prop 已經更新
            this.$nextTick(() => {
              // console.log('Opening modal with selectedReport:', this.selectedReport);
              this.$refs.workflowSettingsModal.showModal();
            });
          } else {
            throw new Error('無法開啟設定視窗');
          }
        } catch (error) {
          console.error('開啟審核流程設定失敗:', error);
          const toast = useToast()
          toast.error('開啟審核流程設定失敗，請稍後再試');
        }
      },
      showContextMenu(event, report) {
        this.showMenu = true;
        this.menuX = event.clientX;
        this.menuY = event.clientY;
        this.selectedReport = report;
      },
      closeContextMenu() {
        this.showMenu = false;
      },
      editReport(report) {
        console.log('編輯報告書:', report);
        // TODO: 實現編輯功能
      },
      downloadReport(report) {
        console.log('下載報告書:', report);
        // TODO: 實現下載功能
      },
      confirmDelete(report) {
        this.selectedReport = report;
        this.showDeleteConfirm = true;
      },
      async deleteReport() {
        // TODO: 實現刪除功能
        console.log('刪除報告書:', this.selectedReport);
        this.showDeleteConfirm = false;
      },
      toggleDropdown(assetID, event) {
        if (this.activeDropdown === assetID) {
          this.activeDropdown = null;
        } else {
          this.activeDropdown = assetID;
          // 等待 DOM 更新後計算位置
          this.$nextTick(() => {
            const button = event.target.closest('.dropdown-toggle');
            const menu = event.target.closest('.dropdown').querySelector('.dropdown-menu');
            if (button && menu) {
              const buttonRect = button.getBoundingClientRect();
              const menuRect = menu.getBoundingClientRect();
              
              // 計算最佳位置
              let top = buttonRect.bottom + window.scrollY;
              let left = buttonRect.right - menuRect.width + window.scrollX;
              
              // 確保選單不會超出視窗底部
              const viewportHeight = window.innerHeight;
              if (top + menuRect.height > viewportHeight) {
                top = buttonRect.top - menuRect.height + window.scrollY;
              }
              
              // 設置選單位置
              menu.style.top = `${top}px`;
              menu.style.left = `${left}px`;
            }
          });
        }
      },
      closeDropdown(event) {
        // 如果點擊的不是下拉選單內的元素，則關閉下拉選單
        if (!event.target.closest('.dropdown')) {
          this.activeDropdown = null;
        }
      },
    },
    watch: {
      selectedReport(newValue) {
        // console.log('selectedReport changed:', newValue);
      }
    },
  }
  </script>
  
  <style scoped>
  .report-management {
    padding: 20px;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
  }
  
  .page-header h1 {
    margin: 0;
    font-size: 24px;
  }
  
  .report-list {
    background-color: #2c2c2c;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .table-container {
    max-height: 600px;
    overflow-y: auto;
    position: relative;
  }
  
  .report-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    color: #fff;
  }
  
  .report-table thead {
    position: sticky;
    top: 0;
    z-index: 1;
    /* background-color: #1a1a1a; */
  }
  
  .report-table th {
    /* text-align: center; */
    text-align: left;
    padding: 16px;
    font-weight: 500;
    color: #888;
    border-bottom: 2px solid #444;
  }
  
  .report-table td {
    padding: 16px;
    border-bottom: 1px solid #333;
  }
  
  .row-hover:hover {
    background-color: rgba(255, 255, 255, 0.05);
    transition: background-color 0.2s ease;
  }
  
  .icon-btn {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 4px;
    background-color: transparent;
    color: #888;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .icon-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #fff;
    transform: scale(1.05);
  }
  
  .icon-btn:active {
    transform: scale(0.95);
  }
  
  .icon-btn.delete:hover {
    color: #ff4444;
  }
  
  .context-menu {
    position: fixed;
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 8px 0;
    min-width: 200px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
  }
  
  .menu-item {
    padding: 8px 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background-color 0.2s;
  }
  
  .menu-item:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .menu-item.delete {
    color: #ff4444;
  }
  
  .menu-item i {
    width: 16px;
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal-content {
    background-color: #2c2c2c;
    border-radius: 8px;
    padding: 24px;
    width: 400px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  }
  
  .modal-content h3 {
    margin: 0 0 16px 0;
    color: #fff;
  }
  
  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
  }
  
  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
  }
  
  .btn.cancel {
    background-color: transparent;
    color: #888;
  }
  
  .btn.cancel:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #fff;
  }
  
  .btn.delete {
    background-color: #ff4444;
    color: #fff;
  }
  
  .btn.delete:hover {
    background-color: #ff6666;
  }
  
  /* 添加波紋效果 */
  @keyframes ripple {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
  
  .icon-btn::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    transform: scale(0);
    opacity: 1;
  }
  
  .icon-btn:active::after {
    animation: ripple 0.6s ease-out;
  }
  
  /* 交替行背景色 */
  .report-table tbody tr:nth-child(even) {
    background-color: rgba(255, 255, 255, 0.02);
  }
  
  .dropdown {
    position: relative;
    display: inline-block;
  }
  
  .dropdown-toggle {
    background: transparent;
    border: none;
    padding: 8px;
    cursor: pointer;
    color: #888;
    transition: all 0.2s;
  }
  
  .dropdown-toggle:hover {
    color: #fff;
  }
  
  .dots {
    font-size: 16px;
    letter-spacing: 1px;
  }
  
  .dropdown-menu {
    position: fixed;
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 4px;
    min-width: 160px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    padding: 8px 0;
  }
  
  .dropdown-menu button {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 16px;
    border: none;
    background: transparent;
    color: #fff;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.2s;
  }
  
  .dropdown-menu button:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .dropdown-menu button.delete {
    color: #ff4444;
  }
  
  .dropdown-menu button.delete:hover {
    background-color: rgba(255, 68, 68, 0.1);
  }
  
  .dropdown-menu button i {
    width: 16px;
  }

  .error-message {
    background-color: rgba(255, 68, 68, 0.1);
    color: #ff4444;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 16px;
  }

  .loading-message {
    color: #888;
    text-align: center;
    padding: 20px;
  }
  </style> 