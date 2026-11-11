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
          <div v-for="s in sessions" :key="s.session_id"
            class="session-item" :class="{ active: s.session_id === sessionId }"
            @click="loadSession(s)">
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
        <div class="no-sessions" v-else><p>暂无对话记录</p></div>
      </template>
    </aside>

    <!-- 右侧：对话区 -->
    <div class="chat-main-wrapper">
      <header class="chat-header">
        <button @click="goBack" class="back-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          <span>返回</span>
        </button>
        <h2>Dify 智能助手</h2>
        <button @click="clearChat" class="clear-btn">清空对话</button>
      </header>

      <main class="chat-main">
        <div ref="messagesContainer" class="chat-messages">
          <div v-for="(msg, idx) in messages" :key="idx"
            :class="['message', msg.role === 'user' ? 'message-user' : 'message-ai']">
            <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
            <div class="message-bubble">
              <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
              <VoicePlay v-if="msg.role === 'ai'" :text="stripMarkdown(msg.content)" class="msg-voice-btn" />
            </div>
          </div>
          <div v-if="streamingText" class="message message-ai">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">
              <div class="message-content" v-html="renderMarkdown(streamingText)"></div>
              <span class="cursor-blink">|</span>
            </div>
          </div>
          <div v-if="messages.length === 0 && !streamingText" class="chat-empty">
            <div class="empty-icon">🤖</div>
            <h3>Dify 智能助手</h3>
            <p>由 Dify Agent + 校园知识库驱动，支持语音输入</p>
            <div class="empty-hints">
              <span>问问课程安排</span>
              <span>查询校园通知</span>
              <span>聊聊学习计划</span>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-row">
            <VoiceInput @recognized="onVoiceRecognized" class="voice-input-btn" />
            <textarea v-model="inputText" @keydown.enter.exact.prevent="sendMessage"
              placeholder="输入消息，或点击麦克风语音输入..." rows="1" class="chat-textarea"
              :disabled="isLoading" ref="inputEl"></textarea>
            <button @click="sendMessage" :disabled="!inputText.trim() || isLoading" class="send-btn">发送</button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import VoiceInput from '../components/VoiceInput.vue'
import VoicePlay from '../components/VoicePlay.vue'
import { listSessions, getSessionMessages, saveMessage, deleteSession } from '../api/history'

const router = useRouter()

const STORAGE_KEY = 'dify_session_id'
function genSessionId() {
  const id = 'dify_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now()
  localStorage.setItem(STORAGE_KEY, id)
  return id
}
const sessionId = ref(localStorage.getItem(STORAGE_KEY) || genSessionId())

const sessions = ref([])
const sidebarCollapsed = ref(false)
const messages = ref([])
const inputText = ref('')
const streamingText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputEl = ref(null)
let conversationId = ''

function goBack() { router.push('/dashboard') }

function clearChat() {
  messages.value = []
  streamingText.value = ''
  conversationId = ''
}

function onVoiceRecognized(text) { inputText.value = text }

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`{3}(\w*)\n?([\s\S]*?)`{3}/g, '<pre><code>$2</code></pre>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function stripMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/`{3}\w*\n?[\s\S]*?`{3}/g, '')
    .replace(/`(.+?)`/g, '$1')
    .replace(/\n/g, ' ')
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', content: text })
  saveMessage(sessionId.value, 'user', text, 'dify').catch(() => {})
  inputText.value = ''
  isLoading.value = true
  streamingText.value = ''

  await nextTick()
  scrollToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const resp = await api.post('/api/dify/agent/chat', {
      query: text,
      conversation_id: conversationId,
      user: 'student',
    }, { headers: { Authorization: `Bearer ${token}` } })

    const answer = resp.data?.answer || '(空回复)'
    conversationId = resp.data?.conversation_id || conversationId
    streamingText.value = ''
    messages.value.push({ role: 'ai', content: answer })
    saveMessage(sessionId.value, 'assistant', answer, 'dify').catch(() => {})
    fetchSessions()
  } catch (e) {
    streamingText.value = ''
    messages.value.push({
      role: 'ai',
      content: 'Dify 智能助手调用失败: ' + (e.response?.data?.detail || e.message),
    })
    if (e.response?.status === 401) { router.push('/login') }
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function fetchSessions() {
  try { sessions.value = ((await listSessions()).data || []).filter(s => s.service_type === 'dify') } catch {}
}

async function loadSession(s) {
  try {
    const res = await getSessionMessages(s.session_id)
    messages.value = (res.data || []).map(m => ({ role: m.role, content: m.content }))
  } catch {}
}

async function handleDeleteSession(sid) {
  try {
    await deleteSession(sid)
    sessions.value = sessions.value.filter(s => s.session_id !== sid)
    if (sessionId.value === sid) { sessionId.value = genSessionId(); messages.value = [] }
  } catch {}
}

function startNewChat() {
  sessionId.value = genSessionId()
  messages.value = []
  streamingText.value = ''
  conversationId = ''
}

onMounted(() => {
  fetchSessions()
  if (inputEl.value) inputEl.value.focus()
})
</script>

<style scoped>
.chat-view { display: flex; height: 100vh; background: #fafafa; }
.history-sidebar {
  width: 260px; background: white; border-right: 1px solid #e4e4e7;
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
  margin: 10px; padding: 8px; background: #3b82f6; color: white; border: none;
  border-radius: 8px; font-size: 13px; cursor: pointer; text-align: center;
}
.new-chat-btn:hover { background: #2563eb; }
.session-list { flex: 1; overflow-y: auto; padding: 0 8px; }
.session-item {
  padding: 10px 8px; border-radius: 6px; cursor: pointer; margin-bottom: 4px;
  border: 1px solid transparent; position: relative; display: flex; flex-direction: column;
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
  display: flex; align-items: center; gap: 12px;
  padding: 12px 20px; background: #fff; border-bottom: 1px solid #e4e4e7;
  flex-shrink: 0;
}
.chat-header h2 { flex: 1; font-size: 16px; font-weight: 600; color: #18181b; }
.back-btn, .clear-btn {
  display: flex; align-items: center; gap: 4px; padding: 6px 12px;
  border: 1px solid #e4e4e7; border-radius: 6px; background: #fff;
  color: #52525b; cursor: pointer; font-size: 13px; transition: all 0.15s;
}
.back-btn:hover, .clear-btn:hover { background: #f4f4f5; }
.chat-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.message { display: flex; gap: 8px; max-width: 80%; }
.message-user { align-self: flex-end; flex-direction: row-reverse; }
.message-ai { align-self: flex-start; }
.message-avatar { width: 32px; height: 32px; font-size: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.message-bubble { position: relative; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-break: break-word; }
.message-user .message-bubble { background: #3b82f6; color: #fff; border-bottom-right-radius: 4px; }
.message-ai .message-bubble { background: #fff; color: #18181b; border: 1px solid #e4e4e7; border-bottom-left-radius: 4px; }
.msg-voice-btn { margin-top: 6px; }
.cursor-blink { animation: blink 1s step-end infinite; color: #3b82f6; }
@keyframes blink { 50% { opacity: 0; } }
.chat-empty { text-align: center; padding: 60px 20px; color: #a1a1aa; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.chat-empty h3 { font-size: 18px; color: #52525b; margin-bottom: 8px; }
.empty-hints { display: flex; gap: 8px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
.empty-hints span { padding: 4px 12px; background: #f4f4f5; border-radius: 12px; font-size: 13px; color: #71717a; }
.chat-input-area { padding: 12px 20px; background: #fff; border-top: 1px solid #e4e4e7; }
.input-row { display: flex; align-items: flex-end; gap: 8px; }
.voice-input-btn { flex-shrink: 0; }
.chat-textarea {
  flex: 1; border: 1px solid #e4e4e7; border-radius: 10px; padding: 10px 14px;
  font-size: 14px; resize: none; outline: none; font-family: inherit; line-height: 1.5;
  min-height: 40px; max-height: 120px; transition: border-color 0.15s;
}
.chat-textarea:focus { border-color: #3b82f6; }
.send-btn {
  padding: 10px 20px; background: #3b82f6; color: #fff; border: none;
  border-radius: 10px; font-size: 14px; font-weight: 500; cursor: pointer;
  transition: background 0.15s; flex-shrink: 0;
}
.send-btn:hover:not(:disabled) { background: #2563eb; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.message-content :deep(pre) { background: #f4f4f5; border-radius: 6px; padding: 10px; overflow-x: auto; margin: 6px 0; }
.message-content :deep(code) { background: #f4f4f5; border-radius: 3px; padding: 1px 4px; font-size: 13px; }
</style>

