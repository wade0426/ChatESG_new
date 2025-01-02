<template>
  <div class="membership-application-review">
    <div class="page-header">
      <h1>人員申請審核 ({{ applications.length }})</h1>
    </div>
    <div class="application-list">
      <table class="application-table">
        <thead>
          <tr>
            <th>申請人</th>
            <th>電子郵件</th>
            <th>帳號建立時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="application in applications" :key="application.email">
            <td class="name-cell">
              <div class="avatar" :style="{ backgroundColor: application.avatarColor }">
                {{ application.name.charAt(0).toUpperCase() }}
              </div>
              <span>{{ application.name }}</span>
            </td>
            <td>{{ application.email }}</td>
            <td>{{ application.createdAt }}</td>
            <td class="action-cell">
              <button class="approve-btn" @click="approveApplication(application.id)" title="允許加入">
                <i class="fas fa-check"></i>
              </button>
              <button class="reject-btn" @click="rejectApplication(application.id)" title="不允許加入">
                <i class="fas fa-times"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MembershipApplicationReview',
  data() {
    return {
      applications: [
        {
          id: 1,
          name: 'John Doe',
          email: 'john@example.com',
          createdAt: '2024-01-15 14:30',
          avatarColor: '#4834d4'
        },
        {
          id: 2,
          name: 'Jane Smith',
          email: 'jane@example.com',
          createdAt: '2024-01-15 15:45',
          avatarColor: '#6ab04c'
        }
      ]
    }
  },
  methods: {
    approveApplication(id) {
      // TODO: 實現允許加入的邏輯
      console.log('Approved application:', id)
    },
    rejectApplication(id) {
      // TODO: 實現拒絕加入的邏輯
      console.log('Rejected application:', id)
    }
  }
}
</script>

<style scoped>
.membership-application-review {
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

.application-list {
  background-color: #2c2c2c;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.application-table {
  width: 100%;
  border-collapse: collapse;
  color: #ffffff;
}

.application-table th {
  text-align: left;
  padding: 12px;
  border-bottom: 1px solid #444;
  color: #888;
  font-weight: normal;
}

.application-table td {
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
  color: white;
  font-weight: bold;
  font-size: 18px;
}

.action-cell {
  display: flex;
  gap: 10px;
}

.approve-btn, .reject-btn {
  padding: 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.approve-btn {
  background-color: #27ae60;
  color: white;
}

.reject-btn {
  background-color: #e74c3c;
  color: white;
}

.approve-btn:hover {
  background-color: #219a52;
}

.reject-btn:hover {
  background-color: #c0392b;
}
</style> 