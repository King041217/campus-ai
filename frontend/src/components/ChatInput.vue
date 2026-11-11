<template>
  <div class="chat-input-area">
    <div class="input-row">
      <textarea
        v-model="text"
        @keydown.enter.exact.prevent="handleSend"
        :placeholder="placeholder || '输入消息，按 Enter 发送...'"
        rows="1"
        class="chat-textarea"
        :disabled="disabled"
        ref="inputEl"
      ></textarea>
      <button
        @click="handleSend"
        :disabled="!text.trim() || disabled"
        class="send-btn"
      >发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['send'])

const text = ref('')
const inputEl = ref(null)

function handleSend() {
  const val = text.value.trim()
  if (!val || props.disabled) return
  emit('send', val)
  text.value = ''
}

onMounted(() => {
  if (inputEl.value) inputEl.value.focus()
})

defineExpose({ clear: () => { text.value = '' }, focus: () => inputEl.value?.focus() })
</script>

<style scoped>
.chat-input-area { border-top: 1px solid #eee; padding: 12px 16px; background: white; }
.input-row { display: flex; gap: 8px; align-items: flex-end; }
.chat-textarea { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 10px; font-size: 14px; resize: none; outline: none; font-family: inherit; line-height: 1.5; max-height: 120px; }
.chat-textarea:focus { border-color: #4477ee; }
.send-btn { padding: 10px 20px; background: #4477ee; color: white; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
.send-btn:hover:not(:disabled) { background: #3366dd; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
