<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import request from '../../../api/request.js'
import { ElMessage } from 'element-plus'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

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

function stopTimer() {
  if (timer.value) clearInterval(timer.value)
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
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">专注计时</h2>
      <ComicBadge variant="primary">ZOOM!</ComicBadge>
    </div>

    <ComicCard class="mx-auto max-w-xl text-center">
      <div class="py-6 font-black text-6xl tracking-wider text-[#1a1a1a] md:text-8xl">{{ displayTime }}</div>
      <div class="flex flex-wrap justify-center gap-3">
        <ComicButton variant="success" size="lg" :disabled="isRunning" @click="start">开始</ComicButton>
        <ComicButton variant="warning" size="lg" :disabled="!isRunning" @click="pause">暂停</ComicButton>
        <ComicButton variant="danger" size="lg" :disabled="!focusSessionId" @click="stop">结束</ComicButton>
      </div>

      <div class="mt-8 space-y-5 text-left">
        <div>
          <div class="mb-2 font-bold">时长（分钟）: {{ duration }}</div>
          <el-slider v-model="duration" :min="5" :max="120" :step="5" show-stops :disabled="isRunning" />
        </div>
        <div>
          <div class="mb-2 font-bold">关联任务</div>
          <el-select v-model="taskId" placeholder="选择任务（可选）" class="w-full" :disabled="isRunning">
            <el-option label="无" :value="null" />
            <el-option v-for="t in tasks" :key="t.id" :label="t.title" :value="t.id" />
          </el-select>
        </div>
        <div>
          <div class="mb-2 font-bold">白噪音</div>
          <el-select v-model="currentNoise" placeholder="选择白噪音" class="w-full">
            <el-option label="无" :value="null" />
            <el-option v-for="n in whiteNoises" :key="n.url" :label="n.name" :value="n.url" />
          </el-select>
        </div>
      </div>
    </ComicCard>
  </div>
</template>

