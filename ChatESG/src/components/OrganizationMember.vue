<template>
  <div class="organization-member">
    <div class="page-header">
      <h1>組織成員 ({{ members.length }})</h1>
      <div class="header-buttons">
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
                <span v-for="role in getMemberRoles(member)" :key="role.roleName" class="role-tag" 
                      :style="{ 
                        backgroundColor: role.roleColor,
                        color: getContrastColor(role.roleColor)
                      }">
                  {{ role.roleName }}
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

    <!-- 使用身份組管理模態框組件 -->
    <RoleManagementModal
      v-model="showRolesModal"
      :roles="roles"
      :members="members"
      @add-role="showAddRoleModal = true"
      @edit-role="editRole"
      @delete-role="deleteRole"
    />

    <!-- 使用編輯成員身份組模態框組件 -->
    <EditMemberRoleModal
      v-model="showEditMemberRolesModal"
      :member="selectedMember"
      :roles="roles"
      :organization-id="organizationId"
      @save="saveMemberRoles"
    />
  </div>
</template>

<script>
import { organizationStore } from '../stores/organization'
import { storeToRefs } from 'pinia'
import { onMounted, ref, computed } from 'vue'
import RoleManagementModal from './RoleManagementModal.vue'
import EditMemberRoleModal from './EditMemberRoleModal.vue'

export default {
  name: 'OrganizationMember',
  components: {
    RoleManagementModal,
    EditMemberRoleModal
  },
  setup() {
    const store = organizationStore()
    const { members, roles, organizationId } = storeToRefs(store)

    // 創建計算屬性來確保返回數組
    const membersList = computed(() => {
      return Array.isArray(members.value) ? members.value : []
    })
    
    const rolesList = computed(() => {
      return Array.isArray(roles.value) ? roles.value : []
    })

    const selectedMember = ref({
      name: '',
      email: '',
      role: []
    })
    const showRolesModal = ref(false)
    const showEditMemberRolesModal = ref(false)
    const showAddRoleModal = ref(false)

    onMounted(async () => {
      await store.initializeOrganization()
    })

    const getMemberRoles = (member) => {
      if (!member?.roles) return [];
      return member.roles;
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const removeMember = (member) => {
      if (confirm(`確定要移除 ${member.name} 嗎？`)) {
        members.value = members.value.filter(m => m.email !== member.email)
      }
    }

    const editMemberRoles = (member) => {
      selectedMember.value = { ...member }; // 創建一個新的對象
      showEditMemberRolesModal.value = true;
    }

    const saveMemberRoles = async (newRoles) => {
      if (selectedMember.value?.email) {
        try {
          const response = await fetch('http://localhost:8000/api/organizations/update_member_roles', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              user_id: selectedMember.value.userID,
              roles: newRoles,
              organization_id: organizationId.value
            })
          });

          const data = await response.json();
          if (data.status === 'success') {
            // 更新本地狀態
            const memberIndex = members.value.findIndex(m => m.email === selectedMember.value.email);
            if (memberIndex !== -1) {
              // 將新的角色轉換為正確的格式
              const updatedRoles = newRoles.map(roleName => {
                const roleInfo = roles.value.find(r => r.roleName === roleName);
                return {
                  roleName: roleName,
                  roleColor: roleInfo ? roleInfo.roleColor : '#3498db'
                };
              });
              members.value[memberIndex].roles = updatedRoles;
            }
          } else {
            throw new Error(data.detail || '更新失敗');
          }
        } catch (error) {
          console.error('更新成員身份組失敗:', error);
          alert('更新失敗: ' + error.message);
        }
      }
    }

    const editRole = (role) => {
      console.log(role)
    }

    const deleteRole = (role) => {
      if (Array.isArray(roles.value)) {
        roles.value = roles.value.filter(r => r !== role)
      }
    }

    const getContrastColor = (hexColor) => {
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
    }

    return { 
      members: membersList,
      roles: rolesList,
      organizationId,
      selectedMember,
      showRolesModal,
      showEditMemberRolesModal,
      showAddRoleModal,
      getMemberRoles,
      formatDate,
      removeMember,
      editMemberRoles,
      saveMemberRoles,
      editRole,
      deleteRole,
      getContrastColor
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
</style> 