<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content">
      <h2>身份組管理</h2>
      <div class="roles-list">
        <div v-for="role in roles" :key="role" class="role-item">
          <div class="role-info">
            <span>{{ role }}</span>
            <span class="member-count">({{ getMemberCountForRole(role) }} 位成員)</span>
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
  </div>
</template>

<script>
export default {
  name: 'RoleManagementModal',
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
  methods: {
    getMemberCountForRole(role) {
      return this.members.filter(member => {
        if (!member?.role) return false;
        const memberRoles = typeof member.role === 'string' ? JSON.parse(member.role) : member.role;
        return memberRoles.includes(role);
      }).length;
    },
    editRole(role) {
      this.$emit('edit-role', role);
    },
    deleteRole(role) {
      if (confirm(`確定要刪除 ${role} 身份組嗎？`)) {
        this.$emit('delete-role', role);
      }
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
</style>
