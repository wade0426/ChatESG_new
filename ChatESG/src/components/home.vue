<template>
    <Sidebar :isOpen="isSidebarOpen" @close="closeNav" />
    <Header @openNav="openNav" />
    
    <!-- 其餘內容保持不變 -->
    <div class="toolbar">
        <router-link to="/asset-overview" class="tool-item">
            <i>📝</i>
            <span>資產總覽</span>
        </router-link>
        <a href="javascript:void(0)" class="tool-item" @click="showCreateCompanyInfoModal">
            <i>📋</i>
            <span>建立公司資料</span>
        </a>
        <a href="javascript:void(0)" class="tool-item" @click="showStandardTemplateModel">
            <i>📊</i>
            <span>建立準則模板</span>
        </a>
        <!-- 建立文件按鈕 -->
        <a href="javascript:void(0)" class="tool-item" @click="showReportModal">
            <i>📄</i>
            <span>建立文件</span>
        </a>
        <a href="javascript:void(0)" class="tool-item" @click="showAddOrganizationModal">
            <i>🌐</i>
            <span>加入組織</span>
        </a>
        <router-link to="/review-list" class="tool-item">
            <i>✔️</i>
            <span>審核</span>
        </router-link>
    </div>

    <!-- 快捷功能區 -->
    <div style="display: flex; justify-content: center; gap: 10px; margin: 20px 0;">
        <button style="background-color: #3A3B3C; border: none; color: white; padding: 8px 16px; border-radius: 20px;">
            📄 測試1
        </button>
        <button style="background-color: #3A3B3C; border: none; color: white; padding: 8px 16px; border-radius: 20px;">
            📄 測試2
        </button>
    </div>

    <!-- 引入彈窗組件 -->
    <ReportModal ref="reportModalRef" />
    <CreateCompanyInfoModal ref="createCompanyInfoModalRef" />
    <AddOrganizationModal ref="addOrganizationModalRef" />
    <StandardTemplateModel ref="standardTemplateModelRef" />

    <!-- 最近設計 -->
    <!-- <div class="recent-designs">
        <h2>最近的報告書</h2>
        <div class="design-grid">
        </div>
    </div> -->
</template>


<script setup>
import { ref } from "vue";
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import ReportModal from './ReportModal.vue'
import CreateCompanyInfoModal from './CreateCompanyInfoModal.vue'
import StandardTemplateModel from './StandardTemplateModel.vue'
import AddOrganizationModal from './AddOrganizationModal.vue'

const isSidebarOpen = ref(false)
const reportModalRef = ref(null)
const createCompanyInfoModalRef = ref(null)
const standardTemplateModelRef = ref(null)
const addOrganizationModalRef = ref(null)

const openNav = () => {
    isSidebarOpen.value = true
}

const closeNav = () => {
    isSidebarOpen.value = false
}

const showReportModal = () => {
    reportModalRef.value.showModal()
}

const showCreateCompanyInfoModal = () => {
    createCompanyInfoModalRef.value.showModal()
}

const showAddOrganizationModal = () => {
    addOrganizationModalRef.value.showModal()
}

const showStandardTemplateModel = () => {
    standardTemplateModelRef.value.showModal()
}
</script>


<style scoped>
/* import 要放在最上面 */
@import "@/assets/home.css";

/* Toolbar 樣式 */
.toolbar {
    display: flex;
    justify-content: center;
    gap: 20px;
    padding: 20px;
    background-color: #242526;
    margin: 20px auto;
    border-radius: 8px;
    max-width: 800px;
}

.tool-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-decoration: none;
    color: white;
    padding: 10px;
    border-radius: 8px;
    transition: background-color 0.3s;
}

.tool-item:hover {
    background-color: #3A3B3C;
}

.tool-item i {
    font-size: 24px;
    margin-bottom: 5px;
}

.tool-item span {
    font-size: 14px;
}

/* 最近設計區域樣式 */
.recent-designs {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.recent-designs h2 {
    margin-bottom: 20px;
    color: white;
}

.design-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}
</style>
