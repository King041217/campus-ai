<template>
  <div class="knowledge-page">
    <button class="back-btn" @click="$router.push('/dashboard')">← 返回首页</button>

    <!-- 左侧：文档管理 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>课件知识库</h2>
        <span class="doc-count" v-if="storeInfo">{{ storeInfo.document_count }} 个文本块</span>
      </div>

      <!-- 上传区域 -->
      <div class="upload-section">
        <label class="upload-label" :class="{ uploading }">
          <input
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            @change="handleFileChange"
            :disabled="uploading"
            hidden
          />
          <span v-if="uploading">上传中...</span>
          <span v-else>+ 上传课件文档</span>
        </label>
        <div class="upload-error" v-if="uploadError" @click="uploadError = ''">
          {{ uploadError }}
        </div>
        <p class="upload-hint">支持 PDF / DOCX / TXT，最大 20MB</p>
      </div>

      <!-- 上传历史 -->
      <div class="history" v-if="uploads.length">
        <h3>上传记录</h3>
        <div class="history-item" v-for="item in uploads" :key="item.file_id">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ item.file_name }}</span>
          <span class="chunk-count">{{ item.chunk_count }} 块</span>
          <button class="delete-doc-btn" @click.stop="handleDeleteDocument(item.file_id)" title="删除此文档">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
          </button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions" v-if="storeInfo && storeInfo.document_count > 0">
        <button class="btn-reset" @click="handleReset">清空知识库</button>
      </div>
    </aside>

    <!-- 右侧：问答区域（使用 MessageList + ChatInput 组件） -->
    <main class="main">
      <div class="chat-header">
        <h3>知识库问答</h3><button class="clear-chat-btn" @click="messages=[]; streamingText=``; localStorage.removeItem(`knowledge_messages`)">清空对话</button>
        <label class="topk-label">
          检索精度(Top-K):
          <select v-model.number="topK">
            <option v-for="k in [1,2,3,4,5,6,7,8,9,10]" :key="k" :value="k">{{ k }} 条</option>
          </select>
          <span title="从向量库中检索 K 条最相关的课件片段，拼接后发给 AI 生成回答。K 越大上下文越丰富，但可能引入噪音。">ⓘ</span>
        </label>
      </div>

      <div class="messages-container" ref="msgContainer">
        <MessageList
          :messages="messages"
          :streamingText="streamingText"
          emptyTitle="上传课件后，在这里向 AI 提问"
          emptyDesc="例如：请介绍数据库的三大范式"
        />
        <div v-if="loading && !streamingText" class="thinking">AI 思考中...</div>
      </div>

      <ChatInput
        :disabled="loading"
        placeholder="输入问题，基于课件内容回答..."
        @send="handleSend"
        ref="chatInputRef"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { uploadDocument, getKnowledgeInfo, resetKnowledge, ragQuery, searchDocs, deleteDocument } from '../api/knowledge'
import MessageList from '../components/MessageList.vue'
import ChatInput from '../components/ChatInput.vue'

const storeInfo = ref(null)
const uploads = reactive([])
const uploading = ref(false)
const uploadError = ref('')
const messages = ref([])
const streamingText = ref('')
const loading = ref(false)
const topK = ref(4)
const msgContainer = ref(null)
const chatInputRef = ref(null)

const hasKnowledge = computed(() => storeInfo.value && storeInfo.value.document_count > 0)

async function fetchInfo() {
  try {
    const res = await getKnowledgeInfo()
    storeInfo.value = res.data
  } catch (e) {
    console.error('获取知识库信息失败:', e)
  }
}

async function handleFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  uploadError.value = ''
  try {
    const res = await uploadDocument(file)
    uploads.push(res.data)
    localStorage.setItem('knowledge_uploads', JSON.stringify(uploads))
    await fetchInfo()
  } catch (e) {
    const detail = e?.response?.data?.detail || e.message || '未知错误'
    uploadError.value = '上传失败: ' + detail
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

async function handleDeleteDocument(fileId) { try { await deleteDocument(fileId); uploads.splice(uploads.findIndex(u => u.file_id === fileId), 1); localStorage.setItem('knowledge_uploads', JSON.stringify(uploads)); } catch {} }

async function handleReset() {
  if (!confirm('确定要清空所有知识库文档吗？此操作不可撤销。')) return
  try {
    await resetKnowledge()
    uploads.splice(0, uploads.length)
    localStorage.removeItem('knowledge_uploads')
    messages.value = []
    streamingText.value = ''
    localStorage.removeItem('knowledge_messages')
    await fetchInfo()
  } catch (e) {
    alert('清空失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleSend(q) {
  if (!q || loading.value) return
  messages.value.push({ role: 'user', content: q })
  loading.value = true

  try {
    // 先检索文档片段
    let sourceCount = 0
    try {
      const searchRes = await searchDocs(q, topK.value)
      sourceCount = searchRes.data?.total || 0
    } catch {}

    // RAG 问答
    const res = await ragQuery(q, topK.value)
    const answer = res.data?.answer || '(空回答)'
    const metadata = { source_count: sourceCount }
    messages.value.push({ role: 'assistant', content: answer, metadata })
    localStorage.setItem('knowledge_messages', JSON.stringify(messages.value))
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '问答失败: ' + (e.response?.data?.detail || e.message),
    })
    localStorage.setItem('knowledge_messages', JSON.stringify(messages.value))
  } finally {
    loading.value = false
  }
}

function scrollToBottom() {
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

onMounted(() => {
  fetchInfo()
  const saved = localStorage.getItem('knowledge_uploads')
  if (saved) { try { uploads.push(...JSON.parse(saved)) } catch {} }
  const msgs = localStorage.getItem('knowledge_messages')
  if (msgs) { try { messages.value = JSON.parse(msgs) } catch {} }
})
</script>

<style scoped>
.knowledge-page {
  display: flex;
  height: calc(100vh - 60px);
  background: #f5f6fa;
  position: relative;
}

.back-btn {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
  background: #fff;
  border: 1px solid #dcdfe6;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
}
.back-btn:hover { background: #f5f7fa; }

/* ---- 左侧边栏 ---- */
.sidebar {
  width: 300px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 16px;
  padding-top: 48px;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.doc-count {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  display: block;
}

.upload-section { text-align: center; }

.upload-label {
  display: block;
  padding: 14px;
  border: 2px dashed #c0c4cc;
  border-radius: 8px;
  cursor: pointer;
  color: #409eff;
  font-size: 14px;
  transition: all 0.2s;
}
.upload-label:hover { border-color: #409eff; background: #ecf5ff; }
.upload-label.uploading { color: #909399; cursor: not-allowed; }

.upload-error {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 6px;
  color: #f56c6c;
  font-size: 12px;
  cursor: pointer;
  word-break: break-all;
}

.upload-hint { font-size: 11px; color: #c0c4cc; margin-top: 6px; }

.history h3 { font-size: 13px; color: #606266; margin: 0 0 8px; }

.history-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  border-bottom: 1px solid #f2f3f5;
  font-size: 13px;
}
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #303133; }
.chunk-count { color: #909399; font-size: 11px; }

.actions { margin-top: auto; }

.btn-reset {
  width: 100%;
  padding: 8px;
  border: 1px solid #f56c6c;
  border-radius: 6px;
  background: #fff;
  color: #f56c6c;
  cursor: pointer;
  font-size: 13px;
}
.btn-reset:hover { background: #fef0f0; }

/* ---- 右侧问答 ---- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}
.chat-header h3 { margin: 0; font-size: 16px; color: #303133; }

.topk-label {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
}
.topk-label select {
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
}
.topk-label span {
  color: #c0c4cc;
  cursor: help;
  font-size: 14px;
  font-style: normal;
}

.messages-container { flex: 1; overflow-y: auto; padding: 20px 24px; }
.thinking { color: #909399; font-size: 13px; padding: 8px 0; }
</style>
