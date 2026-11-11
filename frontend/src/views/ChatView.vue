<template>
  <div class="chat-view">
    <!-- 左侧：历史会话侧栏 -->
    <aside class="history-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <span v-if="!sidebarCollapsed">对话历史</span>
        <button class="toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline v-if="sidebarCollapsed" points="9 18 15 12 9 6"></polyline>
            <polyline v-else points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
      </div>
      <template v-if="!sidebarCollapsed">
        <button class="new-chat-btn" @click="startNewChat">+ 新对话</button>
        <div class="session-list" v-if="sessions.length > 0">
          <div
            v-for="s in sessions" :key="s.session_id"
            class="session-item"
            :class="{ active: s.session_id === sessionId }"
            @click="loadSession(s)"
          >
            <div class="session-title">{{ s.last_message || '(空会话)' }}</div>
            <div class="session-meta">
              <span>{{ s.service_type }}</span>
              <span>{{ s.message_count }} 条</span>
            </div>
            <button class="delete-session-btn" @click.stop="handleDeleteSession(s.session_id)" title="删除会话">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div class="no-sessions" v-else>
          <p>暂无对话记录</p>
        </div>
      </template>
    </aside>

    <!-- 右侧：对话区 -->
    <div class="chat-main-wrapper">
      <header class="chat-header">
        <button @click="goBack" class="back-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          <span>返回</span>
        </button>
        <h2>AI 学伴对话</h2>
        <button @click="clearChat" class="clear-btn">清空对话</button>
      </header>
      <main class="chat-main">
        <MessageList
          :messages="messages"
          :streamingText="streamingText"
          emptyTitle="你好！我是暨小智"
          emptyDesc="你的校园AI学伴，有什么可以帮你的？"
        />
      </main>
      <ChatInput
        :disabled="isLoading"
        placeholder="输入你的问题，按 Enter 发送..."
        @send="sendMessage"
        ref="chatInputRef"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { sendMessageStream } from '../api/chat'
import { listSessions, getSessionMessages, saveMessage, deleteSession } from '../api/history'
import MessageList from '../components/MessageList.vue'
import ChatInput from '../components/ChatInput.vue'

const router = useRouter()

const STORAGE_KEY = 'chat_session_id'

function genSessionId() {
  const id = 'chat_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now()
  localStorage.setItem(STORAGE_KEY, id)
  return id
}

const sessionId = ref(localStorage.getItem(STORAGE_KEY) || genSessionId())

const messages = ref([])
const streamingText = ref('')
const isLoading = ref(false)
const sidebarCollapsed = ref(false)
const sessions = ref([])
const chatInputRef = ref(null)

function goBack() { router.push('/dashboard') }

function clearChat() {
  messages.value = []
  streamingText.value = ''
}

async function sendMessage(text) {
  if (!text || isLoading.value) return
  messages.value.push({ role: 'user', content: text })
  saveMessage(sessionId.value, 'user', text, 'langchain').catch(() => {})
  isLoading.value = true
  streamingText.value = ''

  try {
    const stream = await sendMessageStream(sessionId.value, text)
    const reader = stream.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullContent = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      while (buffer.includes('\n')) {
        const idx = buffer.indexOf('\n')
        const line = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 1)
        if (!line.startsWith('data:')) continue
        try {
          const data = JSON.parse(line.slice(5).trim())
          if (data.error) throw new Error(data.error)
          if (data.done) { fullContent = data.full_content || fullContent; break }
          if (data.delta) { fullContent += data.delta; streamingText.value = fullContent }
        } catch (e) { if (e instanceof SyntaxError) continue; throw e }
      }
    }
    if (fullContent) {
      messages.value.push({ role: 'assistant', content: fullContent })
      saveMessage(sessionId.value, 'assistant', fullContent, 'langchain').catch(() => {})
      fetchSessions()
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，AI 服务暂时不可用：' + e.message })
  } finally {
    streamingText.value = ''
    isLoading.value = false
  }
}

async function fetchSessions() {
  try {
    const res = await listSessions()
    sessions.value = (res.data || []).filter(s => s.service_type === 'langchain')
  } catch { /* ignore */ }
}

async function loadSession(s) {
  try {
    const res = await getSessionMessages(s.session_id)
    messages.value = (res.data || []).map(m => ({ role: m.role, content: m.content }))
  } catch { /* ignore */ }
}

async function handleDeleteSession(sid) {
  try {
    await deleteSession(sid)
    sessions.value = sessions.value.filter(s => s.session_id !== sid)
    if (sessionId.value === sid) {
      sessionId.value = genSessionId()
      messages.value = []
    }
  } catch { /* ignore */ }
}

function startNewChat() {
  sessionId.value = genSessionId()
  messages.value = []
  streamingText.value = ''
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.chat-view { display: flex; height: 100vh; background: #fafafa; }
.history-sidebar {
  width: 260px; background: white; border-right: 1px solid #eee;
  display: flex; flex-direction: column; flex-shrink: 0;
  transition: width 0.2s; overflow: hidden;
}
.history-sidebar.collapsed { width: 40px; }
.sidebar-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 12px; border-bottom: 1px solid #eee; font-weight: 600; font-size: 14px; color: #333;
}
.toggle-btn {
  background: none; border: 1px solid #ddd; border-radius: 4px;
  padding: 4px; cursor: pointer; color: #666; display: flex; align-items: center;
}
.toggle-btn:hover { background: #f5f5f5; }
.new-chat-btn {
  margin: 10px; padding: 8px; background: #4477ee; color: white; border: none;
  border-radius: 8px; font-size: 13px; cursor: pointer; text-align: center;
}
.new-chat-btn:hover { background: #3366dd; }
.session-list { flex: 1; overflow-y: auto; padding: 0 8px; }
.session-item {
  padding: 10px 8px; border-radius: 6px; cursor: pointer; margin-bottom: 4px;
  border: 1px solid transparent; position: relative;
  display: flex; flex-direction: column;
}
.session-item:hover { background: #f4f4f5; }
.session-item.active { background: #eef2ff; border-color: #c7d2fe; }
.session-title { font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px; padding-right: 18px; }
.session-meta { display: flex; gap: 8px; font-size: 11px; color: #999; }
.delete-session-btn {
  position: absolute; top: 6px; right: 6px; background: none; border: none;
  color: #ccc; cursor: pointer; padding: 2px; display: flex; align-items: center;
  opacity: 0; transition: opacity 0.15s;
}
.session-item:hover .delete-session-btn { opacity: 1; }
.delete-session-btn:hover { color: #f56c6c; }
.no-sessions { text-align: center; padding: 30px 12px; color: #aaa; font-size: 13px; }
.chat-main-wrapper { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.chat-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 24px; background: white; border-bottom: 1px solid #eee; flex-shrink: 0;
}
.chat-header h2 { margin: 0; font-size: 18px; color: #333; }
.back-btn {
  display: flex; align-items: center; gap: 4px; padding: 6px 12px;
  border: 1px solid #ddd; border-radius: 6px; background: white; color: #555;
  font-size: 14px; cursor: pointer;
}
.back-btn:hover { background: #f5f5f5; color: #333; }
.clear-btn {
  padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px;
  background: white; color: #888; font-size: 13px; cursor: pointer;
}
.clear-btn:hover { background: #f5f5f5; color: #555; }
.chat-main {
  flex: 1; overflow-y: auto; padding: 20px;
  max-width: 800px; width: 100%; margin: 0 auto;
}
</style>

