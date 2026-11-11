<template>
  <div class="chat-view">
    <header class="chat-header">
      <button @click="goBack" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        <span>返回</span>
      </button>
      <h2>多智能体协作 (Multi-Agent)</h2>
      <button @click="clearChat" class="clear-btn">清空对话</button>
    </header>
    <main class="chat-main">
      <div ref="messagesContainer" class="chat-messages">
        <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role === 'user' ? 'message-user' : 'message-ai']">
          <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="message-bubble">
            <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
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
          <h3>你好！我是校园AI智能助手</h3>
          <p>四 Agent 流水线：分类 → 检索 → 回复 → 质检，不通过自动重试</p>
        </div>
      </div>
      <div class="chat-input-area">
        <div class="input-row">
          <textarea v-model="inputText" @keydown.enter.exact.prevent="sendMessage"
            placeholder="试试：查询Python课程 / 查询我的成绩 / 有哪些自习室 / 最新公告..." rows="1" class="chat-textarea"
            :disabled="isLoading" ref="inputEl"></textarea>
          <button @click="sendMessage" :disabled="!inputText.trim() || isLoading" class="send-btn">发送</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { sendMultiAgentMessage } from '../api/multiAgent'

const router = useRouter()
const messages = ref([])
const inputText = ref('')
const streamingText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputEl = ref(null)
const chatHistory = ref([])

function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n/g, '<br>')
  return html
}

function goBack() {
  router.push('/dashboard')
}

function clearChat() {
  messages.value = []
  chatHistory.value = []
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  messages.value.push({ role: 'user', content: text })
  chatHistory.value.push({ role: 'user', content: text })
  inputText.value = ''
  isLoading.value = true
  streamingText.value = ''
  try {
      const stream = await sendMultiAgentMessage(text)
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
      chatHistory.value.push({ role: 'assistant', content: fullContent })
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，Agent 服务暂时不可用：' + e.message })
  } finally {
    streamingText.value = ''
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

watch(messages, () => { nextTick(() => scrollToBottom()) }, { deep: true })
onMounted(() => { inputEl.value?.focus() })
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; height: 100vh; background: #fafafa; }
.chat-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; background: white; border-bottom: 1px solid #eee; }
.chat-header h2 { margin: 0; font-size: 18px; color: #333; }
.back-btn { display: flex; align-items: center; gap: 4px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; background: white; color: #555; font-size: 14px; cursor: pointer; }
.back-btn:hover { background: #f5f5f5; color: #333; }
.clear-btn { padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px; background: white; color: #888; font-size: 13px; cursor: pointer; }
.clear-btn:hover { background: #f5f5f5; color: #555; }
.chat-main { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; max-width: 800px; margin: 0 auto; width: 100%; }
.chat-empty { text-align: center; margin-top: 80px; color: #666; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.chat-empty h3 { margin: 0 0 8px; color: #333; }
.chat-empty p { margin: 0 0 20px; color: #888; }
.message { display: flex; gap: 10px; max-width: 85%; }
.message-user { align-self: flex-end; flex-direction: row-reverse; }
.message-ai { align-self: flex-start; }
.message-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; background: #f0f0f0; }
.message-bubble { padding: 10px 14px; border-radius: 12px; line-height: 1.6; }
.message-user .message-bubble { background: #4477ee; color: white; border-bottom-right-radius: 4px; }
.message-ai .message-bubble { background: #f5f5f5; border-bottom-left-radius: 4px; }
.message-content :deep(h2) { font-size: 16px; color: #333; margin: 8px 0 4px; }
.message-content :deep(h3) { font-size: 15px; color: #333; margin: 6px 0 4px; }
.message-content :deep(h4) { font-size: 14px; color: #444; margin: 4px 0 2px; }
.message-content :deep(ul) { margin: 4px 0; padding-left: 18px; }
.message-content :deep(li) { margin: 2px 0; }
.message-content :deep(pre) { background: #2d2d2d; color: #e0e0e0; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; margin: 8px 0; }
.message-content :deep(code) { background: rgba(127,127,127,0.15); padding: 1px 4px; border-radius: 3px; font-size: 13px; }
.message-content :deep(pre code) { background: none; padding: 0; }
.cursor-blink { animation: blink 1s infinite; color: #4477ee; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
.chat-input-area { border-top: 1px solid #eee; padding: 12px 16px; background: white; }
.input-row { display: flex; gap: 8px; align-items: flex-end; max-width: 800px; margin: 0 auto; }
.chat-textarea { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 10px; font-size: 14px; resize: none; outline: none; font-family: inherit; line-height: 1.5; max-height: 120px; }
.chat-textarea:focus { border-color: #4477ee; }
.send-btn { padding: 10px 20px; background: #4477ee; color: white; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
.send-btn:hover:not(:disabled) { background: #3366dd; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
