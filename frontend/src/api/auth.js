import api from '../utils/axios'

export function loginApi(data) {
  return api.post('/auth/login', data)
}

export function registerApi(data) {
  return api.post('/auth/register', data)
}

export function getMeApi() {
  return api.get('/auth/me')
}
