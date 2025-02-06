<template>
    <dialog ref="reportModal">
        <div class="modal-content">
            <h3 class="modal-title">建立報告書</h3>
            <form @submit.prevent="createReport" class="report-form">
                <!-- 報告書名稱 -->
                <div class="form-group">
                    <label for="reportName">報告書名稱</label>
                    <input 
                        id="reportName" 
                        v-model="form.reportName" 
                        type="text" 
                        placeholder="輸入報告書名稱"
                        :class="{ error: errors.reportName }"
                    />
                    <span class="error-message" v-if="errors.reportName">
                        {{ errors.reportName }}
                    </span>
                </div>

                <!-- 選擇產業 -->
                <div class="form-group">
                    <label for="industrySelect">產業</label>
                    <select 
                        id="industrySelect" 
                        v-model="form.selectedIndustry"
                        :class="{ error: errors.selectedIndustry }"
                    >
                        <option value="">請選擇產業</option>
                        <option 
                            v-for="industry in reportStore.industries" 
                            :key="industry.value" 
                            :value="industry.value"
                        >
                            {{ industry.label }}
                        </option>
                    </select>
                    <span class="error-message" v-if="errors.selectedIndustry">
                        {{ errors.selectedIndustry }}
                    </span>
                </div>

                <!-- 選擇公司基本資料 -->
                <div class="form-group">
                    <label for="companyAsset">公司基本資料 (資產)</label>
                    <select 
                        id="companyAsset" 
                        v-model="form.selectedAsset"
                        :class="{ error: errors.selectedAsset }"
                    >
                        <option value="">請選擇資產規模</option>
                        <option 
                            v-for="size in reportStore.company_info" 
                            :key="size.value" 
                            :value="size.value"
                        >
                            {{ size.label }}
                        </option>
                    </select>
                    <span class="error-message" v-if="errors.selectedAsset">
                        {{ errors.selectedAsset }}
                    </span>
                </div>

                <!-- 選擇準則模板 -->
                <div class="form-group">
                    <label for="templateSelect">準則模板</label>
                    <select 
                        id="templateSelect" 
                        v-model="form.selectedTemplate"
                        :class="{ error: errors.selectedTemplate }"
                    >
                        <option value="">請選擇準則模板</option>
                        <option 
                            v-for="template in reportStore.templates" 
                            :key="template.value" 
                            :value="template.value"
                        >
                            {{ template.label }}
                        </option>
                    </select>
                    <span class="error-message" v-if="errors.selectedTemplate">
                        {{ errors.selectedTemplate }}
                    </span>
                </div>

                <!-- 動作按鈕 -->
                <div class="modal-actions">
                    <button type="button" class="btn-cancel" @click="hideModal">取消</button>
                    <button 
                        type="submit" 
                        class="btn-confirm"
                        :disabled="reportStore.loading"
                    >
                        {{ reportStore.loading ? '處理中...' : '確認' }}
                    </button>
                </div>
            </form>
        </div>
    </dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useReportStore } from '@/stores/report_model'
import { useUserStore } from '@/stores/user'
import { useFormValidation } from '@/composables/useFormValidation'
import { useToast } from 'vue-toastification'

const reportStore = useReportStore()
const reportModal = ref(null)
const toast = useToast()
const userStore = useUserStore()

const form = reactive({
    reportName: '',
    selectedIndustry: '',
    selectedAsset: '',
    selectedTemplate: ''
})

const { errors, validateForm } = useFormValidation({
    rules: {
        reportName: [
            { required: true, message: '請輸入報告書名稱' },
            { max: 100, message: '報告書名稱不可超過100個字' }
        ],
        selectedIndustry: [
            { required: true, message: '請選擇產業' }
        ],
        selectedAsset: [
            { required: true, message: '請選擇資產規模' }
        ],
        selectedTemplate: [
            { required: true, message: '請選擇準則模板' }
        ]
    }
})

onMounted(async () => {
    // 確保先獲取用戶完整信息
    await userStore.fetchUserProfile()
    // 獲取產業列表
    await reportStore.fetchIndustries()
    // 獲取組織資產
    if (userStore.organizationID) {
        await reportStore.fetchOrganizationAssets(userStore.organizationID)
    } else {
        console.error("未找到組織ID")
    }
})

const showModal = () => {
    if (reportModal.value) {
        reportModal.value.showModal()
    }
}

const hideModal = () => {
    if (reportModal.value) {
        reportModal.value.close()
        // 重置表單
        Object.keys(form).forEach(key => form[key] = '')
        errors.value = {}
    }
}

const createReport = async () => {
    if (!validateForm(form)) return

    try {
        // 获取选中的资产和模板的完整信息
        const selectedAssetInfo = reportStore.company_info.find(item => item.value === form.selectedAsset)
        const selectedTemplateInfo = reportStore.templates.find(item => item.value === form.selectedTemplate)
        const selectedIndustryInfo = reportStore.industries.find(item => item.value === form.selectedIndustry)

        console.log('報告詳細信息：', {
            報告書名稱: form.reportName,
            產業: {
                id: selectedIndustryInfo?.value,
                name: selectedIndustryInfo?.label
            },
            公司基本資料: {
                AssetID: selectedAssetInfo?.value,
                name: selectedAssetInfo?.label
            },
            準則模板: {
                AssetID: selectedTemplateInfo?.value,
                name: selectedTemplateInfo?.label
            }
        })

        toast.success('報告建立成功')
        hideModal()
    } catch (error) {
        toast.error(error.message || '報告建立失敗')
    }
}

defineExpose({
    showModal,
    hideModal
})
</script>

<style scoped>
@import '@/styles/modal.css';
@import '@/styles/form.css';

dialog {
    border: none;
    border-radius: 8px;
    padding: 0;
    background: transparent;
    max-width: 90vw;
    width: 500px;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    margin: 0;
}

dialog::backdrop {
    background: rgba(0, 0, 0, 0.5);
}

.modal-content {
    background-color: #242526;
    border-radius: 8px;
    padding: 24px;
    color: #ffffff;
}

.modal-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 24px 0;
    text-align: center;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-size: 16px;
    color: #ffffff;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid #3A3B3C;
    background-color: #3A3B3C;
    color: #ffffff;
    font-size: 14px;
}

.form-group input::placeholder {
    color: #8E8E8E;
}

.form-group input:focus,
.form-group select:focus {
    outline: none;
    border-color: #4CAF50;
}

.modal-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 24px;
}

.btn-cancel,
.btn-confirm {
    padding: 8px 24px;
    border-radius: 4px;
    border: none;
    font-size: 14px;
    cursor: pointer;
    min-width: 80px;
}

.btn-cancel {
    background-color: #f44336;
    color: white;
}

.btn-confirm {
    background-color: #4CAF50;
    color: white;
}

.btn-confirm:disabled {
    background-color: #8E8E8E;
    cursor: not-allowed;
}

.error-message {
    color: #f44336;
    font-size: 12px;
    margin-top: 4px;
}

.error {
    border-color: #f44336 !important;
}
</style> 