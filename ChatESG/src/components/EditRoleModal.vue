<template>
  <div v-if="modelValue" class="edit-role-modal">
    <div class="modal-content">
      <h2>編輯身份組</h2>
      <div class="form-group">
        <label>身份組名稱</label>
        <input 
          v-model="editedRole.roleName" 
          type="text" 
          placeholder="請輸入身份組名稱"
        >
      </div>
      <div class="form-group">
        <label>顏色</label>
        <input 
          v-model="editedRole.roleColor" 
          type="color"
        >
      </div>
      <div class="buttons">
        <button class="save-btn" @click="saveChanges">保存</button>
        <button class="cancel-btn" @click="$emit('update:modelValue', false)">取消</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EditRoleModal',
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    role: {
      type: Object,
      required: false,
      default: () => ({
        roleName: '',
        roleColor: '#000000'
      })
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      editedRole: {
        originalRoleName: '',
        originalRoleColor: '',
        roleName: '',
        roleColor: ''
      }
    }
  },
  watch: {
    role: {
      immediate: true,
      handler(newRole) {
        if (!newRole) {
          this.editedRole = {
            originalRoleName: '',
            originalRoleColor: '',
            roleName: '',
            roleColor: '#000000'
          }
          return;
        }
        this.editedRole = {
          originalRoleName: newRole.roleName,
          originalRoleColor: newRole.roleColor,
          roleName: newRole.roleName,
          roleColor: newRole.roleColor
        }
      }
    }
  },
  methods: {
    saveChanges() {
      this.$emit('save', this.editedRole)
      this.$emit('update:modelValue', false)
    }
  }
}
</script>

<style scoped>
.edit-role-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
}

.modal-content {
  background-color: #2c2c2c;
  padding: 20px;
  border-radius: 8px;
  min-width: 300px;
  color: white;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input[type="text"] {
  width: 100%;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #444;
  background-color: #3c3c3c;
  color: white;
}

.buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.save-btn, .cancel-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  flex: 1;
}

.save-btn {
  background-color: #007bff;
  color: white;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}
</style> 