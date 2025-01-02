<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content">
      <h2>編輯成員身份組</h2>
      <div class="member-info">
        <span>{{ member?.name }}</span>
        <span> ({{ member?.email }})</span>
      </div>
      <div class="roles-selection">
        <label v-for="role in roles" :key="role" class="role-checkbox">
          <input type="checkbox" 
                 :value="role" 
                 v-model="selectedRoles">
          {{ role }}
        </label>
      </div>
      <div class="modal-actions">
        <button class="save-btn" @click="saveMemberRoles">保存</button>
        <button class="cancel-btn" @click="$emit('update:modelValue', false)">取消</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EditMemberRoleModal',
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    member: {
      type: Object,
      required: true,
      default: () => ({
        name: '',
        email: '',
        role: []
      })
    },
    roles: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      selectedRoles: []
    }
  },
  watch: {
    member: {
      immediate: true,
      handler(newMember) {
        if (newMember?.role) {
          this.selectedRoles = typeof newMember.role === 'string' 
            ? JSON.parse(newMember.role) 
            : newMember.role;
        } else {
          this.selectedRoles = [];
        }
      }
    }
  },
  methods: {
    saveMemberRoles() {
      this.$emit('save', this.selectedRoles);
      this.$emit('update:modelValue', false);
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

.member-info {
  margin: 10px 0;
  color: #888;
}

.roles-selection {
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.role-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.save-btn, .cancel-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn {
  background-color: #28a745;
  color: white;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}
</style>
