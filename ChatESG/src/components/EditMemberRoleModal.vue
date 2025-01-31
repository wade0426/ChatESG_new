<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content">
      <h2>編輯成員身份組</h2>
      <div class="member-info">
        <span>{{ member?.name }}</span>
        <span> ({{ member?.email }})</span>
      </div>
      <div class="roles-selection">
        <div v-if="roles.length === 0" class="no-roles-message">
          目前沒有可用的身份組
        </div>
        <div v-else class="roles-grid">
          <label v-for="role in roles" :key="role.roleName" class="role-checkbox">
            <input type="checkbox" 
                   :value="role.roleName" 
                   v-model="selectedRoles">
            <span class="role-tag" 
                  :style="{
                    backgroundColor: role.roleColor || '#3498db',
                    color: getContrastColor(role.roleColor)
                  }"
                  :class="{ 'role-tag-selected': selectedRoles.includes(role.roleName) }">
              {{ role.roleName }}
              <span class="checkmark" v-if="selectedRoles.includes(role.roleName)">
                ✓
              </span>
            </span>
          </label>
        </div>
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
    },
    organizationId: {
      type: String,
      required: true
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      selectedRoles: [],
      isLoading: false
    }
  },
  watch: {
    member: {
      immediate: true,
      handler(newMember) {
        if (newMember?.roles) {
          this.selectedRoles = newMember.roles.map(role => role.roleName);
        } else {
          this.selectedRoles = [];
        }
      }
    }
  },
  methods: {
    // 根據背景色計算文字顏色
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
    async saveMemberRoles() {
      try {
        this.isLoading = true;
        
        // 檢查必要參數
        console.log('正在發送的數據:', {
          user_id: this.member?.userID,
          roles: this.selectedRoles,
          organization_id: this.organizationId
        });

        if (!this.member?.userID) {
          throw new Error('缺少用戶ID');
        }
        if (!this.selectedRoles || !this.selectedRoles.length) {
          throw new Error('請至少選擇一個身份組');
        }
        if (!this.organizationId) {
          throw new Error('缺少組織ID');
        }

        const response = await fetch('http://localhost:8000/api/organizations/update_member_roles', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: this.member.userID,
            roles: this.selectedRoles,
            organization_id: this.organizationId
          })
        });

        const data = await response.json();
        if (data.status === 'success') {
          this.$emit('save', this.selectedRoles);
          this.$emit('update:modelValue', false);
        } else {
          throw new Error(data.detail || '更新失敗');
        }
      } catch (error) {
        console.error('更新成員身份組失敗:', error);
        alert('更新失敗: ' + error.message);
      } finally {
        this.isLoading = false;
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

.member-info {
  margin: 10px 0;
  color: #888;
}

.roles-selection {
  margin: 20px 0;
  width: 100%;
}

.roles-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

.role-checkbox {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.role-checkbox input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.role-tag {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 2px solid transparent;
}

.role-tag-selected {
  border-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2);
  font-weight: 600;
}

.checkmark {
  font-size: 14px;
  margin-left: 4px;
  font-weight: bold;
}

.role-checkbox input[type="checkbox"]:checked + .role-tag {
  transform: scale(1.02);
}

.role-checkbox:hover .role-tag {
  filter: brightness(1.1);
}

.no-roles-message {
  text-align: center;
  color: #888;
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
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
  opacity: 1;
}

.save-btn:disabled, .cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
