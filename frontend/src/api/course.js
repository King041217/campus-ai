import api from '../utils/axios'

export function listCoursesApi(params) {
  return api.get('/courses', { params })
}

export function getCourseApi(id) {
  return api.get(`/courses/${id}`)
}

export function createCourseApi(data) {
  return api.post('/courses', data)
}

export function updateCourseApi(id, data) {
  return api.put(`/courses/${id}`, data)
}

export function deleteCourseApi(id) {
  return api.delete(`/courses/${id}`)
}
