<!-- 準則檢驗結果顯示組件 -->
<template>
  <div v-if="checkResults && hasValidResults" class="guidelines-result">
    <!-- 符合程度評估區塊 -->
    <div class="result-section compliance-section">
      <div class="compliance-content">
        <h3 class="section-title">
          <i class="mdi mdi-check-circle-outline"></i>
          符合程度評估
        </h3>
        <div :class="['compliance-status', getComplianceClass]">
          <i :class="getComplianceIcon"></i>
          <span>{{ checkResults.符合程度評估 }}</span>
        </div>
      </div>
    </div>

    <!-- 待補充項目區塊 -->
    <div class="result-section supplement-section" v-if="checkResults.待補充項目?.length">
      <h3 class="section-title">
        <i class="mdi mdi-clipboard-list-outline"></i>
        待補充項目
      </h3>
      <div class="supplement-items">
        <div v-for="(item, index) in checkResults.待補充項目" :key="index" class="supplement-card">
          <div class="card-header">
            <div class="header-content">
              <h4 class="item-title">
                <i class="mdi mdi-format-list-checks"></i>
                {{ item.項目 }}
              </h4>
              <span class="gri-tag">
                <i class="mdi mdi-tag-outline"></i>
                {{ item.GRI }}
              </span>
            </div>
          </div>
          <div class="card-content">
            <div class="description">
              <h5>
                <i class="mdi mdi-information-outline"></i>
                說明
              </h5>
              <p>{{ item.說明 }}</p>
            </div>
            <div class="suggestion">
              <h5>
                <i class="mdi mdi-lightbulb-outline"></i>
                建議
              </h5>
              <p class="suggestion-text">{{ item.建議 }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 具體建議區塊 -->
    <div class="result-section suggestions-section" v-if="checkResults.具體建議?.length">
      <h3 class="section-title">
        <i class="mdi mdi-lightbulb-on-outline"></i>
        具體建議
      </h3>
      <div class="suggestions-list">
        <div v-for="(suggestion, index) in checkResults.具體建議" :key="index" class="suggestion-item">
          <i class="mdi mdi-arrow-right-circle-outline"></i>
          <span>{{ suggestion }}</span>
        </div>
      </div>
    </div>

    <!-- 對應 GRI 準則區塊 -->
    <div class="result-section gri-section" v-if="checkResults.對應_GRI_準則?.length">
      <h3 class="section-title">
        <i class="mdi mdi-book-open-page-variant-outline"></i>
        對應 GRI 準則
      </h3>
      <div class="gri-list">
        <div v-for="(gri, index) in checkResults.對應_GRI_準則" :key="index" class="gri-item">
          <i class="mdi mdi-file-document-outline"></i>
          {{ gri }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  checkResults: {
    type: Object,
    default: null
  }
})

// 檢查是否有有效的結果
const hasValidResults = computed(() => {
  if (!props.checkResults) return false
  return props.checkResults.符合程度評估 || 
         (props.checkResults.對應_GRI_準則?.length > 0) ||
         (props.checkResults.待補充項目?.length > 0) ||
         (props.checkResults.具體建議?.length > 0)
})

// 根據符合程度設置不同的樣式類和圖標
const getComplianceClass = computed(() => {
  const status = props.checkResults?.符合程度評估
  switch (status) {
    case '完全符合':
      return 'status-full'
    case '部分符合':
      return 'status-partial'
    case '不符合':
      return 'status-none'
    default:
      return ''
  }
})

const getComplianceIcon = computed(() => {
  const status = props.checkResults?.符合程度評估
  switch (status) {
    case '完全符合':
      return 'mdi mdi-check-circle'
    case '部分符合':
      return 'mdi mdi-alert-circle'
    case '不符合':
      return 'mdi mdi-close-circle'
    default:
      return 'mdi mdi-help-circle'
  }
})
</script>

<style scoped>
.guidelines-result {
  margin-top: 2rem;
  padding: 2rem;
  background-color: var(--bg-color);
  border-radius: 16px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  color: var(--text-color);
}

.result-section {
  margin-bottom: 2.5rem;
  background-color: var(--section-bg-color);
  border-radius: 12px;
  padding: 2rem;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.result-section:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--title-color);
  padding-bottom: 0.75rem;
  border-bottom: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-title i {
  font-size: 1.75rem;
  opacity: 0.9;
}

/* 符合程度評估樣式 */
.compliance-section {
  background: linear-gradient(145deg, var(--section-bg-color), var(--card-bg-color));
  border: none;
  position: relative;
  overflow: hidden;
}

.compliance-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.1), transparent);
  pointer-events: none;
}

.compliance-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.compliance-status {
  font-size: 2rem;
  font-weight: 600;
  padding: 1.5rem 4rem;
  border-radius: 50px;
  display: inline-flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
  margin-top: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.compliance-status i {
  font-size: 2rem;
}

.compliance-status:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.status-full {
  background: linear-gradient(135deg, #059669, #10b981);
  color: white;
}

.status-partial {
  background: linear-gradient(135deg, #d97706, #f59e0b);
  color: white;
}

.status-none {
  background: linear-gradient(135deg, #dc2626, #ef4444);
  color: white;
}

/* GRI 準則列表樣式 */
.gri-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.gri-item {
  padding: 1.25rem 1.5rem;
  background-color: var(--item-bg-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-size: 1rem;
  color: var(--text-color);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.gri-item i {
  font-size: 1.25rem;
  opacity: 0.9;
}

.gri-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--border-hover-color);
}

/* 待補充項目卡片樣式 */
.supplement-items {
  display: grid;
  gap: 1.5rem;
}

.supplement-card {
  background-color: var(--card-bg-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.supplement-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--border-hover-color);
}

.card-header {
  padding: 1.5rem;
  background-color: var(--card-header-bg);
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.item-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--title-color);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.gri-tag {
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: white;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.gri-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.card-content {
  padding: 1.5rem;
  color: var(--text-color);
}

.description, .suggestion {
  margin-bottom: 1.5rem;
}

.description:last-child, .suggestion:last-child {
  margin-bottom: 0;
}

.description h5, .suggestion h5 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--subtitle-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.description p, .suggestion p {
  color: var(--text-color);
  line-height: 1.8;
  margin: 0;
  font-size: 1rem;
  padding-left: 1.75rem;
}

.suggestion-text {
  white-space: pre-line;
}

/* 具體建議列表樣式 */
.suggestions-list {
  display: grid;
  gap: 1rem;
  color: var(--text-color);
}

.suggestion-item {
  padding: 1.25rem 1.5rem;
  background-color: var(--item-bg-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  line-height: 1.8;
  transition: all 0.3s ease;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.suggestion-item i {
  font-size: 1.25rem;
  margin-top: 0.25rem;
  color: var(--subtitle-color);
}

.suggestion-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--border-hover-color);
}

/* 主題變數 */
:deep(.dark) {
  --bg-color: #1a1a1a;
  --section-bg-color: #2d2d2d;
  --title-color: #ffffff;
  --text-color: #e2e8f0;
  --subtitle-color: #94a3b8;
  --border-color: #404040;
  --border-hover-color: #4a5568;
  --item-bg-color: #2d2d2d;
  --card-bg-color: #2d2d2d;
  --card-header-bg: #1a1a1a;
}

:deep(.light) {
  --bg-color: #ffffff;
  --section-bg-color: #f8f9fa;
  --title-color: #1a1a1a;
  --text-color: #4b5563;
  --subtitle-color: #6b7280;
  --border-color: #e2e8f0;
  --border-hover-color: #cbd5e0;
  --item-bg-color: #ffffff;
  --card-bg-color: #ffffff;
  --card-header-bg: #f8f9fa;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .guidelines-result {
    padding: 1.5rem;
  }

  .result-section {
    padding: 1.5rem;
  }

  .section-title {
    font-size: 1.25rem;
  }

  .compliance-status {
    font-size: 1.5rem;
    padding: 1rem 2rem;
  }

  .gri-list {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .gri-tag {
    align-self: flex-start;
    margin-top: 0.5rem;
  }

  .description p, .suggestion p {
    padding-left: 0;
  }
}
</style> 