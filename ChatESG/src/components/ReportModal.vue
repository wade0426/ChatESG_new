<template>
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
                <button @click="hideModal">取消</button>
                <button @click="createReport">建立</button>
            </div>
        </div>
    </dialog>
</template>

<script setup>
import { ref } from 'vue'

const reportModal = ref(null)
const reportName = ref("")
const selectedIndustry = ref("")
const selectedAsset = ref("")
const selectedTemplate = ref("")

const showModal = () => {
    if (reportModal.value) {
        reportModal.value.showModal()
    }
}

const hideModal = () => {
    if (reportModal.value) {
        reportModal.value.close()
    }
}

const createReport = () => {
    console.log("建立報告書：", {
        name: reportName.value,
        industry: selectedIndustry.value,
        asset: selectedAsset.value,
        template: selectedTemplate.value
    })
    hideModal()
}

// 導出方法供父組件使用
defineExpose({
    showModal,
    hideModal
})
</script>

<style scoped>
dialog {
    width: 400px;
    border: none;
    border-radius: 8px;
    background-color: #242526;
    color: white;
    padding: 20px;
    text-align: center;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
}

.createreport_h3 {
    font-size: 1.5em;
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

.modal-actions button:nth-child(1) {
    background-color: #f44336;
}
</style> 