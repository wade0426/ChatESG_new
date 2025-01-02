<template>
  <div class="organization-member">
    <div class="page-header">
      <h1>組織成員 ({{ members.length }})</h1>
      <div class="header-buttons">
        <!-- <button class="add-btn" @click="showAddMemberModal = true">新增成員</button>不使用 -->
        <button class="manage-groups-btn" @click="showRolesModal = true">管理身份組</button>
      </div>
    </div>
    <div class="member-list">
      <table class="member-table">
        <thead>
          <tr>
            <th>姓名</th>
            <th>電子郵件</th>
            <th>加入時間</th>
            <th>身份組</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in members" :key="member.email">
            <td class="name-cell">
              <div class="avatar">
                <img :src="member.avatarUrl" :alt="member.name">
              </div>
              <span>{{ member.name }}</span>
            </td>
            <td>{{ member.email }}</td>
            <td>{{ formatDate(member.joinedAt) }}</td>
            <td>
              <div class="roles-cell">
                <span v-for="role in getMemberRoles(member)" :key="role" class="role-tag">
                  {{ role }}
                </span>
                <button class="edit-groups-btn" @click="editMemberRoles(member)">
                  編輯身份組
                </button>
              </div>
            </td>
            <td>
              <button class="remove-btn" @click="removeMember(member)">移除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 身份組管理彈窗 -->
    <div v-if="showRolesModal" class="modal">
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
        <button class="add-role-btn" @click="showAddRoleModal = true">新增身份組</button>
        <button class="close-btn" @click="showRolesModal = false">關閉</button>
      </div>
    </div>

    <!-- 編輯成員身份組彈窗 -->
    <div v-if="showEditMemberRolesModal" class="modal">
      <div class="modal-content">
        <h2>編輯成員身份組</h2>
        <div class="member-info">
          <span>{{ selectedMember?.name }}</span>
          <span> ({{ selectedMember?.email }})</span>
        </div>
        <div class="roles-selection">
          <label v-for="role in roles" :key="role.name" class="role-checkbox">
            <input type="checkbox" 
                   :value="role" 
                   v-model="selectedRoles">
            {{ role }}
          </label>
        </div>
        <div class="modal-actions">
          <button class="save-btn" @click="saveMemberRoles">保存</button>
          <button class="cancel-btn" @click="showEditMemberRolesModal = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { organizationStore } from '../stores/organization'
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'OrganizationMember',
  setup() {
    const store = organizationStore()
    const router = useRouter()
    const { members, roles } = storeToRefs(store)

    onMounted(async () => {
      await store.initializeOrganization()
    })
    return { members, roles }

  },
  data() {
    return {
      showRolesModal: false,
      showEditMemberRolesModal: false,
      showAddRoleModal: false,
      selectedMember: null,
      selectedRoles: [],
    }
  },
  methods: {
    getMemberRoles(member) {
      if (!member.role) return [];
      return typeof member.role === 'string' ? JSON.parse(member.role) : member.role;
    },
    getMemberCountForRole(role) {
      return this.members.filter(member => {
        const memberRoles = this.getMemberRoles(member);
        return memberRoles.includes(role);
      }).length;
    },
    formatDate(date) {
      return new Date(date).toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    },
    removeMember(member) {
      if (confirm(`確定要移除 ${member.name} 嗎？`)) {
        this.members = this.members.filter(m => m.email !== member.email)
      }
    },
    editMemberRoles(member) {
      this.selectedMember = member;
      this.selectedRoles = this.getMemberRoles(member);
      this.showEditMemberRolesModal = true;
    },
    saveMemberRoles() {
      if (this.selectedMember) {
        const memberIndex = this.members.findIndex(m => m.email === this.selectedMember.email);
        if (memberIndex !== -1) {
          this.members[memberIndex].role = JSON.stringify(this.selectedRoles);
        }
      }
      this.showEditMemberRolesModal = false;
    },
    editRole(role) {
      // 實作編輯身份組邏輯
    //   console.log(this.roles)
      console.log(role)
    },
    deleteRole(role) {
      if (confirm(`確定要刪除 ${role.name} 身份組嗎？`)) {
        this.roles = this.roles.filter(r => r.name !== role.name)
      }
    }
  }
}
</script>

<style scoped>
.organization-member {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #ffffff;
}

.add-btn {
  padding: 8px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.add-btn:hover {
  background-color: #0056b3;
}

.member-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.member-table {
  width: 100%;
  border-collapse: collapse;
  color: #ffffff;
}

.member-table th {
  text-align: left;
  padding: 12px;
  border-bottom: 1px solid #444;
  color: #888;
  font-weight: normal;
}

.member-table td {
  padding: 12px;
  border-bottom: 1px solid #444;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.manage-groups-btn {
  padding: 8px 20px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.manage-groups-btn:hover {
  background-color: #218838;
}

.remove-btn {
  padding: 6px 12px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.remove-btn:hover {
  background-color: #c82333;
}

.roles-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.role-tag {
  background-color: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.edit-groups-btn {
  padding: 4px 8px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

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
</style> 