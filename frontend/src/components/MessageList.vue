<template>
  <div class="message-list">
    <div v-for="(msg, idx) in messages" :key="idx"
      :class="['message', msg.role === 'user' ? 'message-user' : 'message-ai']">
      <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
      <div class="message-bubble">
        <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
        <div v-if="msg.role === 'assistant' && msg.metadata" class="message-meta">
          <span v-if="msg.metadata.cached" class="meta-tag cached">来自缓存</span>
          <span v-if="msg.metadata.service_type" class="meta-tag svc">{{ msg.metadata.service_type }}</span>
        </div>
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
      <h3>{{ emptyTitle || '开始对话' }}</h3>
      <p>{{ emptyDesc || '输入你的问题，AI 助手将为你解答' }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  messages: { type: Array, default: () => [] },
  streamingText: { type: String, default: '' },
  emptyTitle: { type: String, default: '' },
  emptyDesc: { type: String, default: '' },
})

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
</script>

<style scoped>
.message-list { display: flex; flex-direction: column; gap: 16px; }
.message { display: flex; gap: 10px; max-width: 85%; }
.message-user { align-self: flex-end; flex-direction: row-reverse; }
.message-ai { align-self: flex-start; }
.message-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; background: #f0f0f0; }
.message-bubble { padding: 10px 14px; border-radius: 12px; line-height: 1.6; }
.message-user .message-bubble { background: #4477ee; color: white; border-bottom-right-radius: 4px; }
.message-ai .message-bubble { background: #f5f5f5; border-bottom-left-radius: 4px; }
.message-user .message-content :deep(code) { background: rgba(255,255,255,0.2); }
.message-content :deep(h2) { font-size: 16px; margin: 8px 0 4px; }
.message-content :deep(h3) { font-size: 15px; margin: 6px 0 4px; }
.message-content :deep(h4) { font-size: 14px; margin: 4px 0 2px; }
.message-content :deep(ul) { margin: 4px 0; padding-left: 18px; }
.message-content :deep(li) { margin: 2px 0; }
.message-content :deep(pre) { background: #2d2d2d; color: #e0e0e0; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; margin: 8px 0; }
.message-content :deep(code) { background: rgba(127,127,127,0.15); padding: 1px 4px; border-radius: 3px; font-size: 13px; }
.message-content :deep(pre code) { background: none; padding: 0; }
.message-meta { display: flex; gap: 6px; margin-top: 6px; }
.meta-tag { font-size: 11px; padding: 1px 8px; border-radius: 8px; }
.meta-tag.cached { background: #fef3c7; color: #b45309; }
.meta-tag.svc { background: #dbeafe; color: #1d4ed8; }
.cursor-blink { animation: blink 1s infinite; color: #4477ee; }
@keyframes blink { 0%,50% { opacity: 1; } 51%,100% { opacity: 0; } }
.chat-empty { text-align: center; padding: 60px 20px; color: #666; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.chat-empty h3 { margin: 0 0 8px; color: #333; }
.chat-empty p { margin: 0; color: #888; }
</style>
