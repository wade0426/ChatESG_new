<template>
    <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
    <Header @openNav="openNav" />
    
    <!-- 其餘內容保持不變 -->
    <div class="toolbar">
        <a href="#" class="tool-item">
            <i>📋</i>
            <span>公司基本資料</span>
        </a>
        <!-- 建立文件按鈕 -->
        <a href="javascript:void(0)" class="tool-item" @click="showReportModal">
            <i>📄</i>
            <span>建立文件</span>
        </a>
        <a href="#" class="tool-item">
            <i>📊</i>
            <span>簡報</span>
        </a>
        <a href="#" class="tool-item">
            <i>📝</i>
            <span>列印</span>
        </a>
        <a href="#" class="tool-item">
            <i>🌐</i>
            <span>測試</span>
        </a>
        <a href="#" class="tool-item">
            <i>☁️</i>
            <span>上傳</span>
        </a>
    </div>

    <!-- 快捷功能區 -->
    <div style="display: flex; justify-content: center; gap: 10px; margin: 20px 0;">
        <button style="background-color: #3A3B3C; border: none; color: white; padding: 8px 16px; border-radius: 20px;">
            📄 建立文件
        </button>
        <button style="background-color: #3A3B3C; border: none; color: white; padding: 8px 16px; border-radius: 20px;">
            📄 測試
        </button>
    </div>

    <!-- 報告書小視窗 -->
    <dialog ref="reportModal">
        <div class="modal-content">
            <h3 class="createreport_h3">建立報告書</h3>
            <!-- 報告書名稱 -->
            <label for="reportName">報告書名稱</label>
            <input id="reportName" v-model="reportName" type="text" placeholder="輸入報告書名稱" />

            <!-- 選擇產業 -->
            <select id="industrySelect" v-model="selectedIndustry">
                <option value="">請選擇產業</option>
                <option value="finance">金融業</option>
                <option value="technology">科技業</option>
                <option value="manufacturing">製造業</option>
            </select>
            
            <!-- 勾選是否載入預設章節 -->
            <!-- <div class="checkbox-container">
                <label>
                    <span class="checkbox-label">是否自動載入預設章節</span>
                    <input type="checkbox" v-model="autoLoadSections" />
                </label>
            </div> -->

            <!-- 選擇公司基本資料 -->
            <label for="companyAsset">公司基本資料 (資產)</label>
            <select id="companyAsset" v-model="selectedAsset">
                <option value="small">小型企業</option>
                <option value="medium">中型企業</option>
                <option value="large">大型企業</option>
            </select>

            <!-- 選擇準則模板 -->
            <label for="templateSelect">準則模板</label>
            <select id="templateSelect" v-model="selectedTemplate">
                <option value="GRI">GRI 準則</option>
                <option value="SASB">SASB 準則</option>
                <option value="SASB">TCFD 準則</option>
                <option value="SASB">SDGs 永續目標</option>
            </select>

            <!-- 動作按鈕 -->
            <div class="modal-actions">
                <button @click="createReport">建立</button>
                <button @click="hideReportModal">取消</button>
            </div>
        </div>
    </dialog>
    <!-- 最近設計 -->
    <div class="recent-designs">
        <h2>最近的報告書</h2>
        <div class="design-grid">
            <!-- 設計項目將通過 JavaScript 動態添加 -->
        </div>
    </div>
</template>


<script setup>
import { ref } from "vue";
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const isSidebarOpen = ref(false)

const openNav = () => {
    isSidebarOpen.value = true
}

const closeNav = () => {
    isSidebarOpen.value = false
}

// 控制小視窗顯示狀態
const reportModal = ref(null); // 綁定 dialog 元素

const showReportModal = () => {
    if (reportModal.value) {
        reportModal.value.showModal();
    }
};

const hideReportModal = () => {
    if (reportModal.value) {
        reportModal.value.close();
    }
};

// 表單數據
const reportName = ref("");
const selectedIndustry = ref("");
const selectedAsset = ref("");
const selectedTemplate = ref("");
const autoLoadSections = ref(true);

const createReport = () => {
    console.log("建立報告書：", {
        name: reportName.value,
        industry: selectedIndustry.value,
        asset: selectedAsset.value,
        template: selectedTemplate.value,
        autoLoad: autoLoadSections.value,
    });
    hideReportModal(); // 關閉小視窗
};
</script>


<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #18191A;
    color: white;
}

/* 報告書視窗 */
dialog {
    width: 400px;
    border: none;
    border-radius: 8px;
    background-color: #242526;
    color: white;
    padding: 20px;
    text-align: center;

    /* 置中顯示 */
    position: fixed;
    /* 固定在視窗中央 */
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
    /* 添加陰影效果 */
}

.createreport_h3 {
    font-size: 1.5em;
}

/* 勾選框的容器樣式 */
.checkbox-container {
    border: 2px solid #4CAF50;
    /* 綠色邊框 */
    border-radius: 8px;
    /* 圓角 */
    padding: 3px 15px;
    /* 調整內邊距 */
    margin-bottom: 10px;
    /* 與其他元素間距 */
    background-color: #3A3B3C;
    /* 背景顏色 */
    color: white;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    /* 添加陰影 */
    display: flex;
    /* 使用 Flexbox 進行對齊 */
    align-items: center;
    /* 垂直置中 */
}

/* 勾選框放大 */
.checkbox-container input[type="checkbox"] {
    width: 16px;
    /* 調整寬度 */
    height: 16px;
    /* 調整高度 */
    margin-left: 10px;
    /* 與文字之間的距離 */
    cursor: pointer;
    /* 鼠標變成手指 */
}

/* 勾選框旁文字樣式 */
.checkbox-container .checkbox-label {
    font-size: 15px;
    /* 文字大小 */
    font-weight: bold;
    /* 粗體 */
    /*line-height: 0;*/
    /* 保持文字高度與 checkbox 高度一致 */
}


.modal-content label {
    display: block;
    margin: 10px 0 5px;
}

.modal-content input,
.modal-content select {
    width: 100%;
    padding: 8px;
    margin-bottom: 10px;
    background-color: #3A3B3C;
    border: none;
    color: white;
    border-radius: 4px;
}

.modal-actions button {
    margin: 10px 5px;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    background-color: #4CAF50;
    color: white;
}

.modal-actions button:nth-child(2) {
    background-color: #f44336;
}
</style>


<style scoped>
@import "@/assets/home.css";
</style>
