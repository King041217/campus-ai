import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue'),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/courses',
    name: 'courses',
    component: () => import('../views/CourseList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/announcements',
    name: 'announcements',
    component: () => import('../views/AnnouncementList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('../views/KnowledgeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/agent',
    name: 'agent',
    component: () => import('../views/AgentChatView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dify',
    name: 'dify',
    component: () => import('../views/DifyChatView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
