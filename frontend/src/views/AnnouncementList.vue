<template>
  <div class="page">
    <div class="page-header">
      <h2>公告管理</h2>
      <button v-if="userStore.isAdmin" class="btn-primary" @click="showForm = true">+ 发布公告</button>
    </div>

    <div class="announcement-list" v-if="!loading">
      <div v-for="a in announcements" :key="a.id" class="announcement-card" :class="a.priority">
        <div class="ann-header">
          <span class="priority-tag" :class="a.priority">
            {{ a.priority === 'urgent' ? '紧急' : a.priority === 'important' ? '重要' : '普通' }}
          </span>
          <span class="ann-meta">
            {{ a.author }} · {{ formatDate(a.created_at) }}
          </span>
        </div>
        <h3 class="ann-title">{{ a.title }}</h3>
        <p v-if="a.content" class="ann-content">{{ a.content }}</p>
        <div v-if="userStore.isAdmin" class="ann-actions">
          <button class="btn-sm btn-edit" @click="editAnnouncement(a)">编辑</button>
          <button class="btn-sm btn-danger" @click="deleteAnnouncement(a.id)">删除</button>
        </div>
      </div>
      <p v-if="!announcements.length" class="empty">暂无公告</p>
    </div>
    <p v-else class="loading-text">加载中...</p>

    <!-- 编辑弹窗 -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <h3>{{ editingId ? '编辑公告' : '发布公告' }}</h3>
        <form @submit.prevent="saveAnnouncement">
          <div class="form-group">
            <label>标题</label>
            <input v-model="form.title" required />
          </div>
          <div class="form-group">
            <label>发布者</label>
            <input v-model="form.author" />
          </div>
          <div class="form-group">
            <label>优先级</label>
            <select v-model="form.priority">
              <option value="normal">普通</option>
              <option value="important">重要</option>
              <option value="urgent">紧急</option>
            </select>
          </div>
          <div class="form-group">
            <label>内容</label>
            <textarea v-model="form.content" rows="5"></textarea>
          </div>
          <p v-if="formError" class="error-msg">{{ formError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeForm">取消</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'
import { listAnnouncementsApi, createAnnouncementApi, updateAnnouncementApi, deleteAnnouncementApi } from '../api/announcement'

const userStore = useUserStore()
const announcements = ref([])
const loading = ref(true)
const showForm = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')

const form = reactive({
  title: '', content: '', author: '', priority: 'normal',
})

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}

async function fetchAnnouncements() {
  loading.value = true
  try {
    const res = await listAnnouncementsApi()
    announcements.value = res.data
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function editAnnouncement(a) {
  editingId.value = a.id
  Object.assign(form, { title: a.title, content: a.content || '', author: a.author || '', priority: a.priority })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, { title: '', content: '', author: '', priority: 'normal' })
}

async function saveAnnouncement() {
  saving.value = true
  formError.value = ''
  try {
    if (editingId.value) {
      await updateAnnouncementApi(editingId.value, form)
    } else {
      await createAnnouncementApi(form)
    }
    closeForm()
    await fetchAnnouncements()
  } catch (e) {
    formError.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function deleteAnnouncement(id) {
  if (!confirm('确定删除该公告？')) return
  try {
    await deleteAnnouncementApi(id)
    await fetchAnnouncements()
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

onMounted(fetchAnnouncements)
</script>

<style scoped>
.page { padding: 24px 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; font-size: 1.2rem; }
.announcement-list { display: flex; flex-direction: column; gap: 12px; }
.announcement-card {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border-left: 4px solid #e5e7eb;
}
.announcement-card.important { border-left-color: #f59e0b; }
.announcement-card.urgent { border-left-color: #ef4444; }
.ann-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.priority-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}
.priority-tag.normal { background: #f3f4f6; color: #6b7280; }
.priority-tag.important { background: #fef3c7; color: #b45309; }
.priority-tag.urgent { background: #fee2e2; color: #dc2626; }
.ann-meta { font-size: 0.8rem; color: #999; }
.ann-title { font-size: 1rem; margin-bottom: 6px; color: #1a1a2e; }
.ann-content { font-size: 0.9rem; color: #555; line-height: 1.6; white-space: pre-wrap; }
.ann-actions { margin-top: 12px; }
.btn-sm {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  margin-right: 4px;
}
.btn-edit { background: #dbeafe; color: #1d4ed8; }
.btn-danger { background: #fee2e2; color: #dc2626; }
.empty, .loading-text { text-align: center; color: #888; padding: 40px; }
.btn-primary {
  padding: 8px 20px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.btn-primary:disabled { background: #a5b4fc; }
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}
.modal {
  background: white;
  padding: 32px;
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h3 { margin: 0 0 20px; }
.form-group { margin-bottom: 14px; }
.form-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 0.85rem;
  color: #555;
}
.form-group input, .form-group select, .form-group textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}
.form-group textarea { resize: vertical; }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.btn-cancel {
  padding: 8px 20px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
}
.error-msg { color: #ef4444; font-size: 0.85rem; text-align: center; }
</style>
