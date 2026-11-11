export async function sendMultiAgentMessage(message) {
  const token = localStorage.getItem("access_token")
  const response = await fetch("/api/agent/multi/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ message, stream: true }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Request failed")
  }
  return response.body
}
