import api from '../utils/axios'

/** 上传课件文档 */
export function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

/** 获取知识库信息 */
export function getKnowledgeInfo() {
  return api.get('/knowledge/info')
}

/** 清空知识库 */
export function resetKnowledge() {
  return api.delete('/knowledge/reset')
}

/** RAG 问答（非流式） */
export function ragQuery(question, topK = 4) {
  return api.post('/rag/query', { question, top_k: topK, stream: false })
}

/** 检索文档片段（不经过 LLM） */
export function searchDocs(q, topK = 4) {
  return api.get('/rag/search', { params: { q, top_k: topK } })
}


export function deleteDocument(fileId) {
  return api.delete('/knowledge/documents/' + fileId)
}