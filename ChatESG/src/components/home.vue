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
@import "@/assets/home.css";
</style>
