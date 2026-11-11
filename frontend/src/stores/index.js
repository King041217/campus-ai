import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getHello, getHealth } from '../api/hello'

export const useAppStore = defineStore('app', () => {
  const message = ref('')
  const version = ref('')
  const healthStatus = ref('')
  const loading = ref(false)

  async function fetchHello() {
    loading.value = true
    try {
      const res = await getHello()
      message.value = res.data.message
      version.value = res.data.version
    } catch (e) {
      message.value = '连接后端失败: ' + e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchHealth() {
    try {
      const res = await getHealth()
      healthStatus.value = res.data.status
    } catch (e) {
      healthStatus.value = 'unreachable'
    }
  }

  return { message, version, healthStatus, loading, fetchHello, fetchHealth }
})
