import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动注入 Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = "Bearer " + token
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        window.location.href = '/login'
      }
      const detail = data?.detail || data?.message || JSON.stringify(data) || '未知错误'
      return Promise.reject(new Error("[" + status + "] " + detail))
    }
    if (error.code === 'ECONNREFUSED' || (error.message && error.message.indexOf('Network Error') !== -1)) {
      return Promise.reject(new Error('网络错误：后端未启动，请先运行 cd D:\\code\\demo\\backend && .\\venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000'))
    }
    return Promise.reject(new Error('网络错误，请检查连接'))
  }
)

export default api
