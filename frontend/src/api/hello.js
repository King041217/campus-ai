import api from './index'

export function getHello() {
  return api.get('/hello')
}

export function getHealth() {
  return api.get('/health')
}
