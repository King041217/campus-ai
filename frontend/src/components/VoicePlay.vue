<template>
  <button
    :class="['voice-play-btn', { playing: isPlaying, paused: isPaused }]"
    @click="togglePlay"
    :disabled="!supported || !text"
    :title="buttonTitle"
  >
    <svg v-if="!isPlaying" width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="5 3 19 12 5 21 5 3"/>
    </svg>
    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="4" width="4" height="16"/>
      <rect x="14" y="4" width="4" height="16"/>
    </svg>
  </button>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  rate: { type: Number, default: 1.0 },
  pitch: { type: Number, default: 1.0 },
})

const emit = defineEmits(['start', 'end', 'error'])

const isPlaying = ref(false)
const isPaused = ref(false)
const supported = ref(false)

let utterance = null

const synth = window.speechSynthesis
supported.value = !!synth

const buttonTitle = computed(() => {
  if (!supported.value) return '浏览器不支持语音播放'
  if (!props.text) return '暂无内容'
  if (isPlaying.value) return '停止播放'
  return '朗读此消息'
})

function togglePlay() {
  if (!synth) return

  if (synth.speaking && !synth.paused) {
    // 正在播放 → 停止
    synth.cancel()
    isPlaying.value = false
    isPaused.value = false
    emit('end')
    return
  }

  if (synth.paused) {
    // 已暂停 → 恢复
    synth.resume()
    isPlaying.value = true
    isPaused.value = false
    return
  }

  // 新播放
  const text = props.text.trim()
  if (!text) return

  // 取消之前的
  synth.cancel()

  utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'zh-CN'
  utterance.rate = props.rate
  utterance.pitch = props.pitch

  utterance.onstart = () => {
    isPlaying.value = true
    isPaused.value = false
    emit('start')
  }

  utterance.onend = () => {
    isPlaying.value = false
    isPaused.value = false
    emit('end')
  }

  utterance.onerror = (event) => {
    isPlaying.value = false
    isPaused.value = false
    emit('error', event.error)
  }

  synth.speak(utterance)
}

// 组件卸载时清理
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (synth) {
    synth.cancel()
  }
})
</script>

<style scoped>
.voice-play-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #d4d4d8;
  background: #f4f4f5;
  color: #52525b;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  padding: 0;
}

.voice-play-btn:hover:not(:disabled) {
  background: #e4e4e7;
  color: #18181b;
}

.voice-play-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.voice-play-btn.playing {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}

.voice-play-btn.paused {
  background: #f59e0b;
  color: #fff;
  border-color: #f59e0b;
}
</style>
