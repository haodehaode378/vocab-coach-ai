<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import request from '../api/request.js'
import { ElMessage } from 'element-plus'

const duration = ref(25)
const timeLeft = ref(25 * 60)
const timer = ref(null)
const isRunning = ref(false)
const taskId = ref(null)
const tasks = ref([])
const focusSessionId = ref(null)

const whiteNoises = [
  { name: '雨声', url: 'https://cdn.pixabay.com/download/audio/2022/03/24/audio_5c90810042.mp3' },
  { name: '森林', url: 'https://cdn.pixabay.com/download/audio/2022/02/07/audio_18dd463346.mp3' },
]
const currentNoise = ref(null)
const audio = ref(null)

onMounted(async () => {
  const { data } = await request.get('/api/tasks?status=todo')
  tasks.value = data.data
})

onUnmounted(() => {
  stopTimer()
  if (audio.value) audio.value.pause()
})

const displayTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60).toString().padStart(2, '0')
  const s = (timeLeft.value % 60).toString().padStart(2, '0')
  return `${m}:${s}`
})

async function start() {
  if (isRunning.value) return
  timeLeft.value = duration.value * 60
  isRunning.value = true
  const { data } = await request.post('/api/focus/start', {
    duration_minutes: duration.value,
    task_id: taskId.value || null,
  })
  focusSessionId.value = data.data.focus_session_id
  timer.value = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      complete()
    }
  }, 1000)
  playNoise()
}

function pause() {
  if (!isRunning.value) return
  isRunning.value = false
  clearInterval(timer.value)
  if (audio.value) audio.value.pause()
}

async function stop() {
  if (!focusSessionId.value) return
  clearInterval(timer.value)
  isRunning.value = false
  await request.post('/api/focus/end', {
    focus_session_id: focusSessionId.value,
    is_completed: false,
  })
  focusSessionId.value = null
  if (audio.value) audio.value.pause()
  ElMessage.info('已结束专注')
}

async function complete() {
  clearInterval(timer.value)
  isRunning.value = false
  if (focusSessionId.value) {
    await request.post('/api/focus/end', {
      focus_session_id: focusSessionId.value,
      is_completed: true,
    })
    focusSessionId.value = null
  }
  if (audio.value) audio.value.pause()
  ElMessage.success('专注完成！')
}

function playNoise() {
  if (!currentNoise.value) return
  if (!audio.value) audio.value = new Audio()
  audio.value.src = currentNoise.value
  audio.value.loop = true
  audio.value.volume = 0.3
  audio.value.play().catch(() => {})
}
</script>

<template>
  <div>
    <h2>专注计时</h2>
    <el-card style="max-width: 480px; margin-top: 16px; text-align: center;">
      <div style="font-size: 64px; font-weight: 600; letter-spacing: 2px;">{{ displayTime }}</div>
      <div style="margin-top: 16px; display: flex; gap: 10px; justify-content: center;">
        <el-button type="primary" size="large" @click="start" :disabled="isRunning">开始</el-button>
        <el-button size="large" @click="pause" :disabled="!isRunning">暂停</el-button>
        <el-button size="large" @click="stop" :disabled="!focusSessionId">结束</el-button>
      </div>

      <div style="margin-top: 24px; text-align: left;">
        <div style="margin-bottom: 10px;">
          <span>时长（分钟）</span>
          <el-slider v-model="duration" :min="5" :max="120" :step="5" show-stops :disabled="isRunning" />
        </div>
        <div style="margin-bottom: 10px;">
          <span>关联任务</span>
          <el-select v-model="taskId" placeholder="选择任务（可选）" style="width: 100%; margin-top: 6px;" :disabled="isRunning">
            <el-option label="无" :value="null" />
            <el-option v-for="t in tasks" :key="t.id" :label="t.title" :value="t.id" />
          </el-select>
        </div>
        <div>
          <span>白噪音</span>
          <el-select v-model="currentNoise" placeholder="选择白噪音" style="width: 100%; margin-top: 6px;">
            <el-option label="无" :value="null" />
            <el-option v-for="n in whiteNoises" :key="n.url" :label="n.name" :value="n.url" />
          </el-select>
        </div>
      </div>
    </el-card>
  </div>
</template>
