import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getMeApi } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const username = computed(() => userInfo.value?.username || '')
  const role = computed(() => userInfo.value?.role || '')

  function saveToken(newToken) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  function saveUser(user) {
    userInfo.value = user
    localStorage.setItem('user_info', JSON.stringify(user))
  }

  async function login(data) {
    const res = await loginApi(data)
    saveToken(res.data.access_token)
    saveUser(res.data.user)
    return res.data
  }

  async function register(data) {
    const res = await registerApi(data)
    saveToken(res.data.access_token)
    saveUser(res.data.user)
    return res.data
  }

  async function fetchUser() {
    try {
      const res = await getMeApi()
      saveUser(res.data)
      return res.data
    } catch {
      logout()
      return null
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
  }

  return {
    token, userInfo, isLoggedIn, isAdmin, username, role,
    login, register, fetchUser, logout, saveToken, saveUser,
  }
})
