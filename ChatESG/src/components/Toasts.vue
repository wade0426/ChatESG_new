<template>
  <div class="toasts-container">
    <transition-group name="toast">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="toast.type">
        <div class="toast-content">
          <i :class="getIcon(toast.type)"></i>
          <span>{{ toast.message }}</span>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script>
export default {
  name: 'Toasts',
  data() {
    return {
      toasts: [],
      nextId: 0
    }
  },
  methods: {
    getIcon(type) {
      const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle',
        warning: 'fas fa-exclamation-triangle'
      }
      return icons[type] || icons.info
    },
    show(message, type = 'info') {
      const id = this.nextId++
      const toast = {
        id,
        message,
        type
      }
      this.toasts.push(toast)
      setTimeout(() => {
        this.remove(id)
      }, 3000)
    },
    remove(id) {
      const index = this.toasts.findIndex(t => t.id === id)
      if (index > -1) {
        this.toasts.splice(index, 1)
      }
    }
  }
}
</script>

<style scoped>
.toasts-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
}

.toast {
  margin-bottom: 10px;
  padding: 15px 20px;
  min-width: 250px;
  border-radius: 4px;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toast i {
  font-size: 18px;
}

.toast.success {
  background-color: #27ae60;
}

.toast.error {
  background-color: #e74c3c;
}

.toast.info {
  background-color: #3498db;
}

.toast.warning {
  background-color: #f1c40f;
}

/* 動畫效果 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style> 