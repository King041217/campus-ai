<template>
  <div class="page">
    <div class="page-header">
      <h2>课程管理</h2>
      <button v-if="userStore.isAdmin" class="btn-primary" @click="showForm = true">+ 添加课程</button>
    </div>

    <!-- 课程列表 -->
    <div class="table-container" v-if="!loading">
      <table v-if="courses.length">
        <thead>
          <tr>
            <th>课程代码</th>
            <th>课程名称</th>
            <th>授课教师</th>
            <th>学分</th>
            <th>时间地点</th>
            <th v-if="userStore.isAdmin">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in courses" :key="c.id">
            <td>{{ c.code }}</td>
            <td>{{ c.name }}</td>
            <td>{{ c.teacher || '-' }}</td>
            <td>{{ c.credits }}</td>
            <td>{{ c.schedule || '-' }}</td>
            <td v-if="userStore.isAdmin">
              <button class="btn-sm btn-edit" @click="editCourse(c)">编辑</button>
              <button class="btn-sm btn-danger" @click="deleteCourse(c.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">暂无课程数据</p>
    </div>
    <p v-else class="loading-text">加载中...</p>

    <!-- 添加/编辑弹窗 -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <h3>{{ editingId ? '编辑课程' : '添加课程' }}</h3>
        <form @submit.prevent="saveCourse">
          <div class="form-group">
            <label>课程名称</label>
            <input v-model="form.name" required />
          </div>
          <div class="form-group">
            <label>课程代码</label>
            <input v-model="form.code" :disabled="!!editingId" required />
          </div>
          <div class="form-group">
            <label>授课教师</label>
            <input v-model="form.teacher" />
          </div>
          <div class="form-group">
            <label>学分</label>
            <input v-model.number="form.credits" type="number" min="1" max="10" />
          </div>
          <div class="form-group">
            <label>时间地点</label>
            <input v-model="form.schedule" placeholder="例：周一 1-2节 教学楼301" />
          </div>
          <div class="form-group">
            <label>课程描述</label>
            <textarea v-model="form.description" rows="3"></textarea>
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
import { listCoursesApi, createCourseApi, updateCourseApi, deleteCourseApi } from '../api/course'

const userStore = useUserStore()
const courses = ref([])
const loading = ref(true)
const showForm = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')

const form = reactive({
  name: '', code: '', teacher: '', credits: 3, schedule: '', description: '',
})

async function fetchCourses() {
  loading.value = true
  try {
    const res = await listCoursesApi()
    courses.value = res.data
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function editCourse(c) {
  editingId.value = c.id
  Object.assign(form, { name: c.name, code: c.code, teacher: c.teacher || '', credits: c.credits, schedule: c.schedule || '', description: c.description || '' })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, { name: '', code: '', teacher: '', credits: 3, schedule: '', description: '' })
}

async function saveCourse() {
  saving.value = true
  formError.value = ''
  try {
    if (editingId.value) {
      await updateCourseApi(editingId.value, form)
    } else {
      await createCourseApi(form)
    }
    closeForm()
    await fetchCourses()
  } catch (e) {
    formError.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function deleteCourse(id) {
  if (!confirm('确定删除该课程？')) return
  try {
    await deleteCourseApi(id)
    await fetchCourses()
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

onMounted(fetchCourses)
</script>

<style scoped>
.page {
  padding: 24px 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; font-size: 1.2rem; }
.table-container {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 12px 16px;
  text-align: left;
  font-size: 0.9rem;
}
th {
  background: #f9fafb;
  color: #666;
  font-weight: 600;
  border-bottom: 1px solid #eee;
}
td { border-bottom: 1px solid #f0f0f0; }
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
.empty, .loading-text {
  text-align: center;
  color: #888;
  padding: 40px;
}
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
.form-group input, .form-group textarea {
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
.btn-primary {
  padding: 8px 20px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.btn-primary:disabled { background: #a5b4fc; }
.error-msg { color: #ef4444; font-size: 0.85rem; text-align: center; }
</style>
