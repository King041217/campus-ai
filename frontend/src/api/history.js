import api from "../utils/axios"

export function listSessions() {
  return api.get("/history/sessions")
}

export function getSessionMessages(sessionId) {
  return api.get(`/history/session/${sessionId}`)
}

export function deleteSession(sessionId) {
  return api.delete(`/history/session/${sessionId}`)
}

export function saveMessage(sessionId, role, content, serviceType = "langchain") {
  return api.post("/history/save", {
    session_id: sessionId,
    role,
    content,
    service_type: serviceType,
  })
}
