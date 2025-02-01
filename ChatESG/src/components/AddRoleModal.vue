<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content">
      <h2>新增身份組</h2>
      <div class="form-group">
        <label>身份組名稱</label>
        <input 
          v-model="roleData.roleName" 
          type="text" 
          placeholder="請輸入身份組名稱"
        >
      </div>
      <div class="form-group">
        <label>身份組描述</label>
        <textarea 
          v-model="roleData.description" 
          placeholder="請輸入身份組描述"
        ></textarea>
      </div>
      <div class="form-group">
        <label>身份組顏色</label>
        <input 
          v-model="roleData.roleColor" 
          type="color"
        >
      </div>
      <div class="button-group">
        <button class="save-btn" @click="saveRole">新增</button>
        <button class="cancel-btn" @click="$emit('update:modelValue', false)">取消</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AddRoleModal',
  props: {
    modelValue: {
      type: Boolean,
      required: true
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      roleData: {
        roleName: '',
        description: '',
        roleColor: '#007bff'
      }
    }
  },
  methods: {
    saveRole() {
      if (!this.roleData.roleName.trim()) {
        alert('請輸入身份組名稱');
        return;
      }
      this.$emit('save', { ...this.roleData });
      this.$emit('update:modelValue', false);
      // 重置表單
      this.roleData = {
        roleName: '',
        description: '',
        roleColor: '#007bff'
      };
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

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #444;
  border-radius: 4px;
  background-color: #3c3c3c;
  color: white;
}

.form-group textarea {
  height: 100px;
  resize: vertical;
}

.form-group input[type="color"] {
  width: 100%;
  height: 40px;
  padding: 2px;
  border: 1px solid #444;
  border-radius: 4px;
  background-color: #3c3c3c;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.save-btn, .cancel-btn {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
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