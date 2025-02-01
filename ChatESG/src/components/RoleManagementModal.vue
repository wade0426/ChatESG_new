<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content">
      <h2>身份組管理</h2>
      <div class="roles-list">
        <div v-for="role in roles" :key="role" class="role-item">
          <div class="role-info">
            <span class="role-name" :style="{ backgroundColor: role.roleColor, color: getContrastColor(role.roleColor) }">{{ role.roleName }}</span>
            <span class="member-count">({{ getMemberCountForRole(role.roleName) }} 位成員)</span>
          </div>
          <div class="role-actions">
            <button class="edit-btn" @click="editRole(role)">編輯</button>
            <button class="delete-btn" @click="deleteRole(role)">刪除</button>
          </div>
        </div>
      </div>
      <button class="add-role-btn" @click="$emit('add-role')">新增身份組</button>
      <button class="close-btn" @click="$emit('update:modelValue', false)">關閉</button>
    </div>
    <EditRoleModal
      v-model="showEditModal"
      :role="selectedRole"
      @save="handleRoleSave"
    />
  </div>
</template>

<script>
import EditRoleModal from './EditRoleModal.vue'

export default {
  name: 'RoleManagementModal',
  components: {
    EditRoleModal
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    roles: {
      type: Array,
      required: true,
      default: () => []
    },
    members: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  emits: ['update:modelValue', 'add-role', 'edit-role', 'delete-role'],
  data() {
    return {
      showEditModal: false,
      selectedRole: null
    }
  },
  // 頁面載入時，顯示成員資料
  mounted() {
    console.log("roles",this.roles)
    console.log("members",this.members)
  },
  // 計算成員數量
  methods: {
    // 計算擁有特定身份組的成員數量
    // @param {string} role - 要計算的身份組名稱
    // @returns {number} - 擁有該身份組的成員數量
    getMemberCountForRole(roleName) {
      return this.members.filter(member => {
        // 如果成員沒有roles屬性或不是數組，返回false
        if (!Array.isArray(member?.roles)) return false;
        // 檢查該成員的roles數組中是否有匹配的roleName
        return member.roles.some(role => role.roleName === roleName);
      }).length;
    },
    editRole(role) {
      this.selectedRole = role;
      this.showEditModal = true;
    },
    deleteRole(role) {
      if (confirm(`確定要刪除 ${role.roleName} 身份組嗎？`)) {
        this.$emit('delete-role', role);
      }
    },
    getContrastColor(hexColor) {
      if (!hexColor) return '#ffffff';
      
      // 移除 # 符號
      const hex = hexColor.replace('#', '');
      
      // 轉換為 RGB
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      
      // 計算亮度
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      
      // 根據亮度返回黑色或白色
      return brightness > 128 ? '#000000' : '#ffffff';
    },
    handleRoleSave(updatedRole) {
      const roleUpdate = {
        ...updatedRole,
        // originalColor: updatedRole.originalRoleColor, (不使用)
        // newColor: updatedRole.roleColor (不使用)
      };
      this.$emit('edit-role', roleUpdate);
      this.showEditModal = false;
    }
  }
}
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #2c2c2c;
  padding: 20px;
  border-radius: 8px;
  min-width: 400px;
  color: white;
}

.roles-list {
  margin: 20px 0;
}

.role-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #444;
}

.role-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-count {
  color: #888;
  font-size: 14px;
}

.role-actions {
  display: flex;
  gap: 8px;
}

.edit-btn, .delete-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-btn {
  background-color: #ffc107;
  color: black;
}

.delete-btn {
  background-color: #dc3545;
  color: white;
}

.add-role-btn {
  width: 100%;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.close-btn {
  margin-top: 20px;
  padding: 8px 16px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
}

.role-name{
  padding: 4px 8px;
  border-radius: 8px;
  background-color: #007bff;
  color: white;
}
</style>
