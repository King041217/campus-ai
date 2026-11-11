<template>
  <div class="home">
    <h1>校园AI助手平台</h1>
    <p class="subtitle">Campus AI Assistant Platform</p>

    <div class="card">
      <h2>前后端联调测试</h2>
      <p class="status" v-if="appStore.healthStatus">
        后端状态：
        <span :class="appStore.healthStatus === 'ok' ? 'green' : 'red'">
          {{ appStore.healthStatus === 'ok' ? '正常运行' : '异常' }}
        </span>
      </p>
      <button @click="testConnection" :disabled="appStore.loading">
        {{ appStore.loading ? '请求中...' : '测试后端连接' }}
      </button>
      <p v-if="appStore.message" class="result">
        后端回复：<strong>{{ appStore.message }}</strong>
        <span v-if="appStore.version" class="version">(v{{ appStore.version }})</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAppStore } from '../stores'

const appStore = useAppStore()

async function testConnection() {
  await appStore.fetchHello()
}

onMounted(() => {
  appStore.fetchHealth()
})
</script>

<style scoped>
.home {
  max-width: 600px;
  margin: 60px auto;
  text-align: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
h1 {
  font-size: 2rem;
  color: #1a1a2e;
  margin-bottom: 4px;
}
.subtitle {
  color: #888;
  margin-bottom: 40px;
  font-size: 0.95rem;
}
.card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 32px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.card h2 {
  font-size: 1.1rem;
  color: #333;
  margin-bottom: 16px;
}
.status {
  margin-bottom: 16px;
  font-size: 0.9rem;
  color: #555;
}
.green { color: #22c55e; font-weight: 600; }
.red { color: #ef4444; font-weight: 600; }
button {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 10px 28px;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
button:hover { background: #4338ca; }
button:disabled { background: #a5b4fc; cursor: not-allowed; }
.result {
  margin-top: 20px;
  font-size: 1rem;
  color: #333;
}
.version {
  color: #888;
  font-size: 0.85rem;
  margin-left: 6px;
}
</style>
