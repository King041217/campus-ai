import api from '../utils/axios'

export function listAnnouncementsApi(params) {
  return api.get('/announcements', { params })
}

export function getAnnouncementApi(id) {
  return api.get(`/announcements/${id}`)
}

export function createAnnouncementApi(data) {
  return api.post('/announcements', data)
}

export function updateAnnouncementApi(id, data) {
  return api.put(`/announcements/${id}`, data)
}

export function deleteAnnouncementApi(id) {
  return api.delete(`/announcements/${id}`)
}
