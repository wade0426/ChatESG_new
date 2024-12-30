<!-- - **公司基本資料編輯頁面 (CompanyInfoEdit.vue)**
     - 編輯公司的基本資料
     - 儲存和取消編輯功能
     - 使用 Tiptap：基於 ProseMirror，可以輕鬆擴展版本控制。
     - 使用 Y.js：支持實時協作和版本管理，與 Quill 整合較為順暢。 -->

<template>
  <div :class="['editor-container', theme]">
    <!-- 側邊欄 -->
    <div class="sidebar-wrapper">
      <div :class="['sidebar', { 'collapsed': isSidebarCollapsed }]">
        <div class="sidebar-header">
          <h3>公司基本資料表</h3>
          <button @click="toggleSidebar" class="sidebar-toggle">
            <i :class="['mdi', isSidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left']"></i>
          </button>
        </div>
        <div class="sidebar-content">
          <template v-for="(section, index) in sections" :key="section.id">
            <!-- 大標題 -->
            <div class="section-level-1">
              <div 
                :class="['section-title', { 'active': selectedSection === section.id }]"
                @click="toggleSection(section.id)"
              >
                <div class="section-title-content">
                  <span>{{ index + 1 }}. {{ section.title }}</span>
                  <i :class="['mdi', isExpanded(section.id) ? 'mdi-chevron-down' : 'mdi-chevron-right']"></i>
                </div>
              </div>
              
              <!-- 子標題 -->
              <template v-if="section.children && isExpanded(section.id)">
                <div 
                  v-for="(subSection, subIndex) in section.children" 
                  :key="subSection.id"
                  class="section-level-2"
                >
                  <div 
                    :class="['section-title', { 'active': selectedSection === subSection.id }]"
                    @click="toggleSubSection(subSection.id)"
                  >
                    <div class="section-title-content">
                      <span>{{ getAlphabetLabel(subIndex) }}. {{ subSection.title }}</span>
                      <i v-if="subSection.children" :class="['mdi', isExpanded(subSection.id) ? 'mdi-chevron-down' : 'mdi-chevron-right']"></i>
                    </div>
                  </div>
                  
                  <!-- 內容項目 -->
                  <div v-if="subSection.children" :class="{ 'hidden': !isExpanded(subSection.id) }">
                    <div 
                      v-for="(item, itemIndex) in subSection.children" 
                      :key="item.id"
                      class="section-level-3"
                    >
                      <div 
                        :class="['section-title', { 'active': selectedSection === item.id }]"
                        @click.stop="selectSection(item.id)"
                      >
                        <div class="section-title-content">
                          <span>{{ getRomanNumeral(itemIndex + 1) }}. {{ item.title }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 主要編輯區域 -->
    <div :class="['main-content', { 'expanded': isSidebarCollapsed }]">
      <div class="editor-header">
        <div class="header-content">
          <h2>{{ getCurrentSectionTitle() }}</h2>
          <div class="theme-toggle">
            <button @click="toggleTheme" class="theme-button">
              <i :class="['mdi', theme === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny']"></i>
            </button>
          </div>
        </div>
      </div>
      
      <div class="editor-content">
        <editor-content 
          :editor="getCurrentEditor()" 
          class="tiptap-editor"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Editor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'

// 側邊欄狀態
const isSidebarCollapsed = ref(false)
const selectedSection = ref('about')
const theme = ref('dark')
const expandedSections = ref(new Set())

// 章節結構
const sections = [
  {
    id: 'about',
    title: '關於本報告書',
    children: [
      {
        id: 'about-section',
        title: '關於本報告書',
        children: [
          { id: 'company-name', title: '公司名稱' },
          { id: 'report-period', title: '報告期間' },
          { id: 'scope-boundary', title: '範疇與邊界' },
          { id: 'report-principles', title: '報告書撰寫原則' },
          { id: 'contact-info', title: '聯絡資訊' }
        ]
      }
    ]
  },
  {
    id: 'sustainability',
    title: '永續發展策略',
    children: [
      {
        id: 'governance',
        title: '永續治理架構',
        children: [
          { id: 'committee', title: '永續發展委員會' }
        ]
      },
      {
        id: 'blueprint',
        title: '永續發展藍圖',
        children: [
          { id: 'strategy-pillars', title: '永續策略主軸' },
          { id: 'sustainability-goals', title: '永續目標' }
        ]
      },
      {
        id: 'material-topics',
        title: '重大主題分析',
        children: [
          { id: 'identification-process', title: '重大主題鑑別流程' },
          { id: 'topic-management', title: '重大主題管理' }
        ]
      },
      {
        id: 'stakeholder-communication',
        title: '利害關係人溝通',
        children: [
          { id: 'stakeholder-identification', title: '利害關係人鑑別' },
          { id: 'stakeholder-engagement', title: '利害關係人議和' }
        ]
      }
    ]
  }
]

// 編輯器配置
const createEditor = (content = '') => new Editor({
  extensions: [
    StarterKit,
    Table.configure({ resizable: true }),
    TableRow,
    TableCell,
    TableHeader
  ],
  content,
  editorProps: {
    attributes: {
      class: 'prose prose-lg max-w-none',
    }
  }
})

// 為每個章節創建編輯器實例
const editors = {}
sections.forEach(section => {
  editors[section.id] = createEditor()
  if (section.children) {
    section.children.forEach(subSection => {
      editors[subSection.id] = createEditor()
      if (subSection.children) {
        subSection.children.forEach(item => {
          editors[item.id] = createEditor()
        })
      }
    })
  }
})

// 方法
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
}

const selectSection = (sectionId) => {
  selectedSection.value = sectionId
}

const getCurrentEditor = () => {
  return editors[selectedSection.value]
}

const getCurrentSectionTitle = () => {
  const section = findSectionById(selectedSection.value, sections)
  return section ? section.title : '';
}

const findSectionById = (id, sectionsArray) => {
  for (const section of sectionsArray) {
    if (section.id === id) {
      return section;
    }
    if (section.children) {
      const foundInChildren = findSectionById(id, section.children);
      if (foundInChildren) {
        return foundInChildren;
      }
    }
  }
  return null;
}

const save = () => {
  // 實作儲存邏輯
  console.log('儲存內容')
}

const cancel = () => {
  // 實作取消邏輯
  console.log('取消編輯')
}

// 輔助函數：將數字轉換為字母標籤 (A, B, C...)
const getAlphabetLabel = (index) => {
  return String.fromCharCode(65 + index);
}

// 輔助函數：將數字轉換為羅馬數字
const getRomanNumeral = (num) => {
  const romanNumerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x'];
  return romanNumerals[num - 1] || num;
}

// 初始化展開狀態
const initializeExpandedSections = () => {
  sections.forEach(section => {
    expandedSections.value.add(section.id)
    if (section.children) {
      section.children.forEach(subSection => {
        // 預設不展開子標題
        // expandedSections.value.add(subSection.id)
      })
    }
  })
}

// 在組件掛載時初始化
onMounted(() => {
  initializeExpandedSections()
})

const toggleSection = (sectionId) => {
  const newExpandedSections = new Set(expandedSections.value);
  if (newExpandedSections.has(sectionId)) {
    newExpandedSections.delete(sectionId);
    // 收合直接子節點
    const section = sections.find(s => s.id === sectionId);
    if (section && section.children) {
      section.children.forEach(child => newExpandedSections.delete(child.id));
    }
  } else {
    newExpandedSections.add(sectionId);
  }
  expandedSections.value = newExpandedSections;
  selectSection(sectionId);
}

const toggleSubSection = (sectionId) => {
  const newExpandedSections = new Set(expandedSections.value);
  if (newExpandedSections.has(sectionId)) {
    newExpandedSections.delete(sectionId);
  } else {
    newExpandedSections.add(sectionId);
  }
  expandedSections.value = newExpandedSections;
  selectSection(sectionId);
}

const isExpanded = (sectionId) => {
  return expandedSections.value.has(sectionId)
}
</script>


<style scoped>
.editor-container {
  display: flex;
  min-height: 100vh;
  transition: all 0.3s ease;
  background-color: #ffffff;
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  overflow-y: auto;
}

.editor-container.dark {
  background-color: #1a1a1a;
}

.sidebar-wrapper {
  position: relative;
  z-index: 2;
}

.sidebar {
  width: 280px;
  height: 100vh;
  transition: all 0.3s ease;
  position: relative;
  background-color: #f8f9fa;
  border-right: 1px solid #e2e8f0;
}

.dark .sidebar {
  background-color: #1a1a1a;
  border-right: 1px solid #2d2d2d;
}

.sidebar.collapsed {
  width: 0;
}

.sidebar.collapsed .sidebar-content,
.sidebar.collapsed .sidebar-header h3 {
  opacity: 0;
  visibility: hidden;
}

.sidebar-header {
  height: 60px;
  padding: 0 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  border-bottom: 1px solid #e2e8f0;
  min-width: 280px;
}

.dark .sidebar-header {
  border-bottom: 1px solid #2d2d2d;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  white-space: nowrap;
}

.dark .sidebar-header h3 {
  color: #ffffff;
}

.sidebar-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: fixed;
  left: 268px;
  top: 30px;
  transform: translateY(-50%);
  z-index: 1000;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.dark .sidebar-toggle {
  background-color: #ffffff;
  border: 1px solid #404040;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.sidebar-toggle:hover {
  transform: translateY(-50%) scale(1.1);
}

.section-level-1 {
  margin-bottom: 1rem;
}

.section-level-2 {
  padding-left: 1.5rem;
  margin-top: 0.5rem;
}

.section-level-3 {
  padding-left: 1.5rem;
  margin-top: 0.25rem;
}

.section-title {
  padding: 0.5rem 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.section-title:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .section-title:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.section-title.active {
  background-color: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}

.dark .section-title.active {
  background-color: rgba(96, 165, 250, 0.1);
  color: #60a5fa;
}

.light .section-level-1 > .section-title {
  font-weight: 600;
  color: #1a1a1a;
}

.dark .section-level-1 > .section-title {
  font-weight: 600;
  color: #ffffff;
}

.light .section-level-2 > .section-title {
  font-weight: 500;
  color: #2d3748;
}

.dark .section-level-2 > .section-title {
  font-weight: 500;
  color: #e2e8f0;
}

.light .section-level-3 > .section-title {
  font-weight: 400;
  color: #4a5568;
}

.dark .section-level-3 > .section-title {
  font-weight: 400;
  color: #cbd5e0;
}

.light .section-title {
  color: #000000;
}

.dark .section-title {
  color: #ffffff;
}

.light .section-title:hover {
  background-color: #e2e8f0;
}

.light .section-title.active {
  background-color: #e2e8f0;
  color: #2563eb;
}

.dark .section-title:hover {
  background-color: #2d2d2d;
}

.dark .section-title.active {
  background-color: #2d2d2d;
  color: #60a5fa;
}

.main-content {
  flex: 1;
  padding: 2rem;
  transition: all 0.3s ease;
  margin: 1rem;
  position: relative;
  min-height: calc(100vh - 2rem);
  overflow-y: auto;
}

.light .main-content {
  background-color: #ffffff;
  color: #000000;
}

.dark .main-content {
  background-color: #1a1a1a;
  color: #ffffff;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.light .header-content {
  color: #000000;
}

.dark .header-content {
  color: #ffffff;
}

.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.light .theme-button {
  color: #4b5563;
}

.dark .theme-button {
  color: #ffffff;
}

.theme-button:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.dark .theme-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.tiptap-editor {
  border-radius: 8px;
  min-height: 300px;
  padding: 1rem;
}

.light .tiptap-editor {
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  color: #000000;
}

.dark .tiptap-editor {
  border: 1px solid #2d2d2d;
  background-color: #1a1a1a;
  color: #e2e8f0;
}

.dark .tiptap-editor p {
  color: #e2e8f0;
}

.dark .tiptap-editor * {
  color: #e2e8f0;
}

.mdi {
  line-height: 1;
  vertical-align: middle;
  font-size: 1.2rem;
}

.light h2 {
  color: #000000;
}

.dark h2 {
  color: #ffffff;
}

.sidebar.collapsed + .main-content {
  margin-left: 0;
}

.sidebar.collapsed .sidebar-toggle {
  left: 0;
}

.section-title-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.section-title-content i {
  font-size: 1rem;
  transition: transform 0.3s ease;
}

.hidden {
  display: none;
}
</style>