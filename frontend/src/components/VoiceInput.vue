<template>
  <div class="voice-input">
    <button
      :class="['voice-btn', { recording: isRecording }]"
      @click="toggleRecording"
      :disabled="!supported"
      :title="supported ? '点击开始/停止语音输入' : '浏览器不支持语音识别'"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" y1="19" x2="12" y2="23"/>
        <line x1="8" y1="23" x2="16" y2="23"/>
      </svg>
    </button>
    <div v-if="interimText" class="interim-text">{{ interimText }}</div>
    <div v-if="!supported" class="not-supported">⚠ 浏览器不支持语音识别（请用 Chrome）</div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const emit = defineEmits(['recognized'])

const isRecording = ref(false)
const interimText = ref('')
const supported = ref(false)

let recognition = null

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

if (SpeechRecognition) {
  supported.value = true
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.interimResults = true
  recognition.continuous = true
  recognition.maxAlternatives = 1

  recognition.onresult = (event) => {
    let final = ''
    let interim = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      if (result.isFinal) {
        final += result[0].transcript
      } else {
        interim += result[0].transcript
      }
    }
    interimText.value = interim
    if (final) {
      emit('recognized', final.trim())
      interimText.value = ''
    }
  }

  recognition.onerror = (event) => {
    if (event.error === 'no-speech') {
      interimText.value = '未检测到语音...'
    } else if (event.error === 'aborted') {
      // 用户主动停止，正常
    } else {
      interimText.value = '识别错误: ' + event.error
    }
    isRecording.value = false
  }

  recognition.onend = () => {
    isRecording.value = false
  }
}

function toggleRecording() {
  if (!recognition) return
  if (isRecording.value) {
    recognition.stop()
    isRecording.value = false
    interimText.value = ''
  } else {
    recognition.start()
    isRecording.value = true
    interimText.value = ''
  }
}

onUnmounted(() => {
  if (recognition && isRecording.value) {
    recognition.stop()
  }
})
</script>

<style scoped>
.voice-input {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.voice-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid #d4d4d8;
  background: #f4f4f5;
  color: #52525b;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.voice-btn:hover {
  background: #e4e4e7;
  color: #18181b;
}

.voice-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.voice-btn.recording {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}

.interim-text {
  font-size: 13px;
  color: #71717a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.not-supported {
  font-size: 12px;
  color: #ef4444;
}
</style>
