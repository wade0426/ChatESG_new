<template>
  <!-- 側邊欄 -->
  <div id="mySidebar" class="sidebar">
      <a href="javascript:void(0)" class="close-btn" @click="closeNav">&times;</a>
      <a href="#" class="sidebar-item" style="display: none;">首頁</a>
      <a href="#" class="sidebar-item" style="display: none;">我的設計</a>
      <a href="#" class="sidebar-item" style="display: none;">模板庫</a>
      <a href="#" class="sidebar-item" style="display: none;">設定</a>
  </div>

  <!-- 頂部導航欄 -->
  <div class="header">
      <div class="menu-icon" @click="openNav">
          <div></div>
          <div></div>
          <div></div>
      </div>
      <div class="search-bar">
          <div class="search-icon">
              <svg viewBox="0 0 24 24">
                  <path
                      d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
              </svg>
          </div>
          <input type="text" placeholder="搜尋您的內容。">
      </div>
      <div class="user-profile" @click="toggleDropdown">
          <div class="user-avatar" id="user-avatar"></div>
          <div class="user-info">
              <span class="organization-name" id="organization-name"></span>
              <span class="user-name" id="user-name"></span>
          </div>
          <span class="dropdown-arrow">▼</span>
          <div class="dropdown-menu" id="userDropdown">
              <div class="dropdown-menu-content">
                  <a href="#"><span>帳號</span></a>
                  <a href="#"><span>邀請成員</span></a>
                  <div class="menu-divider"></div>
                  <a href="#"><span>設定</span></a>
                  <a href="#"><span>最新消息</span></a>
                  <a href="#"><span>方案和定價</span></a>
                  <a href="#"><span>建議改善事項</span></a>
                  <a href="#"><span>檢舉內容</span></a>
                  <a href="#"><span>隱私權政策</span></a>
                  <div class="menu-divider"></div>
                  <a href="#" @click="logout"><span>登出</span></a>
              </div>
          </div>
      </div>
  </div>

  <div class="toolbar">
      <a href="/" class="tool-item">
          <i>📄</i>
          <span>建立文件</span>
      </a>
      <a href="#" class="tool-item">
          <i>📋</i>
          <span>公司資料</span>
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

  <!-- 最近設計 -->
  <div class="recent-designs">
      <h2>最近的報告書</h2>
      <div class="design-grid">
          <!-- 設計項目將通過 JavaScript 動態添加 -->
      </div>
  </div>
</template>


<script setup>
const openNav = () => {
  document.getElementById("mySidebar").style.width = "250px";
  // 裡面的內容延遲顯示
  setTimeout(() => {
    const sidebarItems = document.getElementsByClassName("sidebar-item");
    if (sidebarItems && sidebarItems.length > 0) {
      for (let item of sidebarItems) {
        item.style.display = "block";
      }
    }
  }, 150);
}

const closeNav = () => {
  document.getElementById("mySidebar").style.width = "0";
  const sidebarItems = document.getElementsByClassName("sidebar-item");
    if (sidebarItems && sidebarItems.length > 0) {
      for (let item of sidebarItems) {
        item.style.display = "none";
      }
    }
}

const toggleDropdown = () => {
  document.getElementById("userDropdown").classList.toggle("show");
}

const logout = () => {
  // 實作登出邏輯
  console.log("登出");
}
</script>


<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #18191A;
    color: white;
}
</style>


<style scoped>
/* 頂部導航欄 */
.header {
    display: flex;
    align-items: center;
    padding: 12px 24px;
    background-color: #242526;
    justify-content: space-between;
}

.search-bar {
    flex: 1;
    margin: 0 20px;
    position: relative;
    max-width: 720px;
}

.search-bar input {
    width: 100%;
    padding: 12px 44px;
    border-radius: 8px;
    border: 1px solid;
    background-color: #242526;
    color: #E4E6EB;
    font-size: 15px;
    outline: none;
    transition: background-color 0.2s;
}

.search-bar input:focus {
    background-color: #3A3B3C;
}

.search-bar input::placeholder {
    color: #B0B3B8;
}

/* 搜索圖標 */
.search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #B0B3B8;
    display: flex;
    align-items: center;
}

.search-icon svg {
    width: 20px;
    height: 20px;
    fill: currentColor;
}

/* 工具欄 */
.toolbar {
    display: flex;
    justify-content: center;
    padding: 16px;
    gap: 20px;
}

.tool-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    color: white;
    text-decoration: none;
    padding: 8px;
    border-radius: 8px;
}

.tool-item:hover {
    background-color: #3A3B3C;
}

/* 最近設計區域 */
.recent-designs {
    padding: 24px;
    margin: 0 10%;
}

.recent-designs h2 {
    margin-bottom: 20px;
}

.design-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.design-item {
    background-color: #242526;
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: background-color 0.2s;
}

.design-item:hover {
    background-color: #3A3B3C;
}

.design-info {
    display: flex;
    align-items: center;
    flex: 1;
    gap: 16px;
    min-width: 0;
}

.design-name {
    flex: 2;
    font-size: 14px;
    color: #E4E6EB;
    white-space: normal;
    word-wrap: break-word;
    min-width: 0;
    max-width: 45%;
}

.design-author {
    flex: 1;
    font-size: 14px;
    color: #B0B3B8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 45%;
}

.design-time {
    font-size: 14px;
    color: #B0B3B8;
    white-space: nowrap;
}

.design-status {
    flex: 1;
    font-size: 14px;
    max-width: 8%;
    text-align: center;
}

.design-actions {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-left: 16px;
}

.star-button {
    background: none;
    border: none;
    color: #B0B3B8;
    cursor: pointer;
    padding: 4px;
}

.star-button:hover {
    color: #E4E6EB;
}

.more-options {
    background: none;
    border: none;
    color: #B0B3B8;
    cursor: pointer;
    padding: 4px;
}

.more-options:hover {
    color: #E4E6EB;
}

/* 漢堡選單圖標樣式 */
.menu-icon {
    cursor: pointer;
    padding: 10px;
    margin-right: 10px;
}

.menu-icon div {
    width: 25px;
    height: 3px;
    background-color: white;
    margin: 5px 0;
    transition: 0.4s;
}

/* 側邊欄樣式 */
.sidebar {
    height: 100%;
    width: 0;
    position: fixed;
    z-index: 1;
    top: 0;
    left: 0;
    background-color: #242526;
    overflow-x: hidden;
    transition: 0.5s;
    padding-top: 60px;
}

.sidebar a {
    padding: 8px 8px 8px 32px;
    text-decoration: none;
    font-size: 18px;
    color: #818181;
    display: block;
    transition: 0.3s;
}

.sidebar a:hover {
    color: #f1f1f1;
}

.sidebar .close-btn {
    position: absolute;
    top: 0;
    right: 25px;
    font-size: 36px;
    margin-left: 50px;
}

/* 用戶資料樣式 */
.user-profile {
    position: relative;
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
}

.user-profile:hover {
    background-color: #3A3B3C;
}

.user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: #FF4B4B;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    margin-right: 8px;
}

.user-info {
    display: flex;
    flex-direction: column;
    margin-right: 8px;
}

.organization-name {
    font-size: 14px;
    color: #B0B3B8;
}

.user-name {
    font-size: 14px;
    color: white;
}

.dropdown-arrow {
    margin-left: 4px;
}

/* 下拉選單樣式 */
.dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    background-color: #242526;
    border-radius: 8px;
    padding: 8px 0;
    min-width: 200px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    display: none;
    z-index: 1000;
}

.dropdown-menu.show {
    display: block;
}

.dropdown-menu a {
    padding: 8px 16px;
    color: #E4E6EB;
    text-decoration: none;
    display: flex;
    align-items: center;
}

.dropdown-menu a:hover {
    background-color: #3A3B3C;
}

.menu-divider {
    height: 1px;
    background-color: #3A3B3C;
    margin: 8px 0;
}

/* 添加更多選項下拉選單的樣式 */
.more-options-menu {
    position: absolute;
    right: 0;
    background-color: #242526;
    border-radius: 8px;
    padding: 8px 0;
    min-width: 200px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    display: none;
    z-index: 1000;
}

.more-options-menu.show {
    display: block;
}

.more-options-menu a {
    padding: 8px 16px;
    color: #E4E6EB;
    text-decoration: none;
    display: flex;
    align-items: center;
    font-size: 14px;
}

.more-options-menu a:hover {
    background-color: #3A3B3C;
}

.more-options-menu .menu-divider {
    height: 1px;
    background-color: #3A3B3C;
    margin: 4px 0;
}

.design-actions {
    position: relative;
}
</style>
