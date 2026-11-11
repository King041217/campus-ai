<template>
  <div class="dashboard">
    <header class="dash-header">
      <div class="header-left">
        <h1>校园AI助手</h1>
        <span class="welcome">欢迎回来，{{ userStore.userInfo?.full_name || userStore.username }}</span>
      </div>
      <div class="header-right">
        <span class="role-badge" :class="userStore.role">{{ roleLabel }}</span>
        <button class="btn-logout" @click="handleLogout">退出登录</button>
      </div>
    </header>

    <nav class="dash-nav">
      <a v-for="item in navItems" :key="item.label"
         class="nav-item" :class="{ active: currentView === item.view }"
         @click="handleNavClick(item)">
        {{ item.label }}
      </a>
    </nav>

    <main class="dash-content">

      <!-- 管理员端：总览 -->
      <div v-if="currentView === 'admin-home'" class="section">
        <div class="stats-grid">
          <div class="stat-card" @click="currentView = 'courses'">
            <div class="stat-number">{{ stats.courses }}</div>
            <div class="stat-label">课程总数</div>
          </div>
          <div class="stat-card" @click="currentView = 'announcements'">
            <div class="stat-number">{{ stats.announcements }}</div>
            <div class="stat-label">公告总数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ stats.users }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </div>
        <div class="info-section">
          <h3>平台状态</h3>
          <div class="info-grid">
            <div class="info-item"><span class="label">当前用户</span><span class="value">{{ userStore.username }}</span></div>
            <div class="info-item"><span class="label">用户角色</span><span class="value">{{ roleLabel }}</span></div>
            <div class="info-item"><span class="label">API 地址</span><span class="value">http://localhost:8000</span></div>
            <div class="info-item"><span class="label">系统版本</span><span class="value">v0.1.0</span></div>
          </div>
        </div>
      </div>

      <!-- 学生端首页 -->
      <div v-if="currentView === 'student-home'" class="section">
        <div class="feature-grid">
          <div class="feature-card" style="cursor:pointer" @click="router.push('/chat')">
            <div class="feature-icon">&#x1F4AC;</div>
            <h3>AI 对话助手</h3>
            <p>与校园 AI 助手进行自然语言对话，解答课程、校园生活等问题</p>
            <span class="feature-badge active">可用</span>
          </div>
         <div class="feature-card" style="cursor:pointer" @click="router.push('/agent')">
            <div class="feature-icon">&#x1F916;</div>
            <h3>AI 智能体 (Agent)</h3>
            <p>自主调用工具查询课程、成绩、自习室、公告，体验 Function Calling</p>
            <span class="feature-badge active">Day 6 新功能</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="router.push('/knowledge')">
            <div class="feature-icon">&#x1F4DA;</div>
            <h3>知识库问答</h3>
            <p>基于课程资料的知识库检索问答，快速找到学习答案</p>
            <span class="feature-badge active">可用</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="currentView = 'courses'">
            <div class="feature-icon">&#x1F4D6;</div>
            <h3>课程查询</h3>
            <p>查看课程列表、课程详情、上课时间安排</p>
            <span class="feature-badge active">可用</span>
          </div>
         <div class="feature-card" style="cursor:pointer" @click="currentView = 'announcements'">
            <div class="feature-icon">&#x1F4E2;</div>
            <h3>校园公告</h3>
            <p>查看学校发布的最新公告和通知</p>
            <span class="feature-badge active">可用</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="router.push('/dify')">
            <div class="feature-icon">&#x1F9E0;</div>
            <h3>Dify 智能助手</h3>
            <p>Dify Agent 驱动的校园助手，支持语音对话和知识库检索</p>
            <span class="feature-badge active">Day 9 新功能</span>
          </div>
        </div>
      </div>

      <!-- 教师端首页 -->
      <div v-if="currentView === 'teacher-home'" class="section">
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">&#x1F9E0;</div>
            <h3>AI 教学辅助</h3>
            <p>利用 AI 辅助备课、出题、批改作业等教学任务</p>
            <span class="feature-badge coming">即将上线</span>
          </div>
          <div class="feature-card">
            <div class="feature-icon">&#x1F4AC;</div>
            <h3>答疑管理</h3>
            <p>查看和管理学生的提问，AI 辅助回答常见问题</p>
            <span class="feature-badge coming">即将上线</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="currentView = 'courses'">
            <div class="feature-icon">&#x1F4D6;</div>
            <h3>课程管理</h3>
            <p>管理课程信息、查看课程列表</p>
            <span class="feature-badge active">可用</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="currentView = 'announcements'">
            <div class="feature-icon">&#x1F4E2;</div>
            <h3>公告管理</h3>
            <p>发布和管理校园公告通知</p>
            <span class="feature-badge active">可用</span>
          </div>
        </div>
      </div>

      <!-- 决策者端首页 -->
      <div v-if="currentView === 'decision-home'" class="section">
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">&#x1F4CA;</div>
            <h3>学情分析大屏</h3>
            <p>ECharts 可视化大屏展示课程咨询量、问题分布、满意度趋势</p>
            <span class="feature-badge coming">即将上线</span>
          </div>
          <div class="feature-card">
            <div class="feature-icon">&#x1F525;</div>
            <h3>知识点热度图</h3>
            <p>展示热门知识点、高频问题词云、学科关注度分布</p>
            <span class="feature-badge coming">即将上线</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="currentView = 'courses'">
            <div class="feature-icon">&#x1F4D6;</div>
            <h3>课程概览</h3>
            <p>查看所有课程列表和数据统计</p>
            <span class="feature-badge active">可用</span>
          </div>
          <div class="feature-card" style="cursor:pointer" @click="currentView = 'announcements'">
            <div class="feature-icon">&#x1F4E2;</div>
            <h3>公告查看</h3>
            <p>查看学校发布的公告通知</p>
            <span class="feature-badge active">可用</span>
          </div>
        </div>
      </div>

      <!-- 课程管理 -->
      <CourseList v-if="currentView === 'courses'" />
      <!-- 公告管理 -->
      <AnnouncementList v-if="currentView === 'announcements'" />

    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { listCoursesApi } from '../api/course'
import api from '../utils/axios'
import CourseList from './CourseList.vue'
import AnnouncementList from './AnnouncementList.vue'

const router = useRouter()
const userStore = useUserStore()

const currentView = ref('home')
const stats = ref({ courses: 0, announcements: 0, users: 0 })

const roleLabel = computed(() => {
  const map = { student: '学生', teacher: '教师', admin: '管理员', decision_maker: '决策者' }
  return map[userStore.userInfo?.role] || userStore.userInfo?.role || ''
})

const navItems = computed(() => {
  const role = userStore.userInfo?.role
  if (role === 'admin') return [
    { label: '总览', view: 'admin-home' },
    { label: '课程', view: 'courses' },
    { label: '公告', view: 'announcements' },
    { label: '知识库', view: 'knowledge', route: '/knowledge' },
    { label: 'AI学伴', view: 'chat', route: '/chat' },
    { label: 'Agent', view: 'agent', route: '/agent' },
    { label: 'Dify', view: 'dify', route: '/dify' },
  ]
  if (role === 'student') return [
    { label: '首页', view: 'student-home' },
    { label: '课程', view: 'courses' },
    { label: '公告', view: 'announcements' },
    { label: '知识库', view: 'knowledge', route: '/knowledge' },
    { label: 'AI学伴', view: 'chat', route: '/chat' },
    { label: 'Agent', view: 'agent', route: '/agent' },
    { label: 'Dify', view: 'dify', route: '/dify' },
  ]
  if (role === 'teacher') return [
    { label: '首页', view: 'teacher-home' },
    { label: '课程', view: 'courses' },
    { label: '公告', view: 'announcements' },
    { label: '知识库', view: 'knowledge', route: '/knowledge' },
    { label: 'AI学伴', view: 'chat', route: '/chat' },
    { label: 'Agent', view: 'agent', route: '/agent' },
    { label: 'Dify', view: 'dify', route: '/dify' },
  ]
  if (role === 'decision_maker') return [
    { label: '大屏', view: 'decision-home' },
    { label: '课程', view: 'courses' },
    { label: '公告', view: 'announcements' },
    { label: '知识库', view: 'knowledge', route: '/knowledge' },
    { label: 'AI学伴', view: 'chat', route: '/chat' },
    { label: 'Agent', view: 'agent', route: '/agent' },
    { label: 'Dify', view: 'dify', route: '/dify' },
  ]
  return [{ label: '首页', view: 'home' }]
})

onMounted(async () => {
  const role = userStore.userInfo?.role
  if (role === 'admin') currentView.value = 'admin-home'
  else if (role === 'student') currentView.value = 'student-home'
  else if (role === 'teacher') currentView.value = 'teacher-home'
  else if (role === 'decision_maker') currentView.value = 'decision-home'

  try {
    listCoursesApi().then(res => { stats.value.courses = res.data?.length || 0 }).catch(() => {})
    api.get('/announcements').then(res => { stats.value.announcements = res.data?.length || 0 }).catch(() => {})
    api.get('/auth/users').then(res => { stats.value.users = res.data?.total || 0 }).catch(() => {})
  } catch { /* ignore */ }
})

function handleNavClick(item) {
  if (item.route) {
    router.push(item.route)
  } else {
    currentView.value = item.view
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard { min-height: 100vh; background: #f5f5f5; }
.dash-header {
  background: white; padding: 16px 32px;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.header-left h1 { font-size: 1.3rem; color: #1a1a2e; margin: 0; }
.welcome { font-size: 0.85rem; color: #888; margin-left: 8px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.role-badge { padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 500; }
.role-badge.student { background: #dbeafe; color: #1d4ed8; }
.role-badge.teacher { background: #dcfce7; color: #15803d; }
.role-badge.admin { background: #fef3c7; color: #b45309; }
.role-badge.decision_maker { background: #e0e7ff; color: #4338ca; }
.btn-logout {
  background: none; border: 1px solid #ddd; padding: 6px 16px;
  border-radius: 6px; cursor: pointer; color: #666; font-size: 0.9rem;
}
.btn-logout:hover { background: #f5f5f5; }
.dash-nav { background: white; padding: 0 32px; display: flex; border-bottom: 1px solid #eee; }
.nav-item {
  padding: 12px 20px; font-size: 0.9rem; cursor: pointer; color: #666;
  border-bottom: 2px solid transparent; user-select: none;
}
.nav-item:hover { color: #4f46e5; }
.nav-item.active { color: #4f46e5; border-bottom-color: #4f46e5; font-weight: 500; }
.dash-content { padding: 24px 32px; max-width: 1000px; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: white; padding: 24px; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); text-align: center; cursor: pointer;
}
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.stat-number { font-size: 2rem; font-weight: 700; color: #4f46e5; }
.stat-label { font-size: 0.85rem; color: #888; margin-top: 4px; }
.info-section { background: white; padding: 24px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.info-section h3 { margin: 0 0 16px; font-size: 1rem; color: #333; }
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.info-item {
  display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0;
}
.info-item .label { color: #888; font-size: 0.9rem; }
.info-item .value { color: #333; font-weight: 500; font-size: 0.9rem; }
.feature-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.feature-card {
  background: white; padding: 28px 24px; border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); transition: box-shadow 0.2s, transform 0.15s;
}
.feature-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); transform: translateY(-2px); }
.feature-icon { font-size: 2rem; margin-bottom: 12px; }
.feature-card h3 { font-size: 1rem; margin-bottom: 8px; color: #1a1a2e; }
.feature-card p { font-size: 0.85rem; color: #777; line-height: 1.5; margin-bottom: 12px; }
.feature-badge { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 0.75rem; font-weight: 500; }
.feature-badge.active { background: #dcfce7; color: #15803d; }
.feature-badge.coming { background: #f3f4f6; color: #9ca3af; }
.section { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
