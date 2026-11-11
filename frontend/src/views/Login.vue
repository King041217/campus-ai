<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>登录</h2>
      <p class="subtitle">校园AI助手平台</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="请输入用户名" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码" required />
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <p class="auth-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  loading.value = true
  errorMsg.value = ''
  try {
    await userStore.login(form)
    router.push('/dashboard')
  } catch (e) {
    errorMsg.value = e.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f2f5;
}
.auth-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  width: 100%;
  max-width: 400px;
}
.auth-card h2 {
  text-align: center;
  margin-bottom: 4px;
  color: #1a1a2e;
}
.subtitle {
  text-align: center;
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 24px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
}
.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
}
.form-group input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79,70,229,0.1);
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { background: #a5b4fc; cursor: not-allowed; }
.error-msg {
  color: #ef4444;
  font-size: 0.85rem;
  margin-bottom: 12px;
  text-align: center;
}
.auth-link {
  text-align: center;
  margin-top: 20px;
  font-size: 0.9rem;
  color: #666;
}
.auth-link a {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 500;
}
</style>
