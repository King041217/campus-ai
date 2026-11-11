import api from "../utils/axios"

const BASE = "/chat"

export async function sendMessageStream(sessionId, message, template = "ai_buddy") {
  const token = localStorage.getItem("access_token")
  const response = await fetch("/api/langchain/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({
      session_id: sessionId,
      user_input: message,
      stream: true,
      template,
    }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Request failed")
  }
  return response.body
}

export function listTemplates() {
  return api.get(BASE + "/templates")
}

export async function sendAgentMessage(message, history = []) {
  const token = localStorage.getItem("access_token")
  const response = await fetch("/api/agent/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({
      message,
      history,
      stream: true,
    }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Request failed")
  }
  return response.body
}
