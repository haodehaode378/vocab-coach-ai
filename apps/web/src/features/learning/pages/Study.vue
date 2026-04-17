<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '../../../api/request.js'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAppStore } from '../../../stores/app.js'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicPanel from '../../../components/comic/ComicPanel.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

const router = useRouter()
const store = useAppStore()
const queue = ref([])
const currentIndex = ref(0)
const showMeaning = ref(false)
const loading = ref(false)
const finished = ref(false)
const stats = ref({ review_count: 0, new_count: 0 })
const testLoading = ref(false)
const currentBookName = computed(() => store.currentBookTag || '全部词库')

onMounted(async () => {
  await store.loadCurrentBook()
  await loadQueue()
})

async function loadQueue() {
  loading.value = true
  const { data } = await request.get('/api/study/today')
  queue.value = data.data.queue
  stats.value = { review_count: data.data.review_count, new_count: data.data.new_count }
  currentIndex.value = 0
  showMeaning.value = false
  finished.value = queue.value.length === 0
  loading.value = false
}

const current = computed(() => queue.value[currentIndex.value])
const progressText = computed(() => {
  const total = queue.value.length
  const done = currentIndex.value
  const curr = current.value
  if (!curr) return ''
  const typeLabel = curr.is_new ? '新词' : '复习'
  return `${typeLabel} ${done + 1} / ${total}`
})

function revealMeaning() {
  showMeaning.value = true
}

async function grade(response) {
  if (!current.value) return
  await request.post('/api/study/grade', {
    vocab_item_id: current.value.id,
    response,
    session_type: current.value.is_new ? 'learn' : 'review',
  })

  if (response === 'vague') {
    ElMessage({ message: '该词将在稍后（约 10 分钟）再次出现', type: 'warning', plain: true })
  } else if (response === 'forget') {
    ElMessage({ message: '该词将在稍后（约 5 分钟）再次出现', type: 'warning', plain: true })
  }

  showMeaning.value = false
  if (currentIndex.value < queue.value.length - 1) {
    currentIndex.value++
  } else {
    finished.value = true
    ElMessage.success('今日学习任务完成！')
  }
}

async function startTest() {
  testLoading.value = true
  try {
    const { data } = await request.post('/api/study/test/generate')
    const payload = data.data
    localStorage.setItem('daily_test_session', JSON.stringify(payload))
    router.push('/practice?source=daily_test')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally {
    testLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">今日学习</h2>
      <ComicBadge variant="warning">GO!</ComicBadge>
    </div>

    <p v-if="loading" class="py-8 text-center font-black text-[#1a1a1a]">加载中...</p>

    <div v-else-if="finished" class="py-10">
      <ComicPanel action-lines class="mx-auto max-w-xl text-center">
        <div class="mb-2 text-6xl">🎉</div>
        <div class="font-black text-3xl uppercase tracking-wide text-[#1a1a1a]">今日学习完成</div>
        <div class="mt-2 font-bold text-[#1a1a1a]/80">继续保持，积少成多</div>
        <div class="mt-6 flex justify-center gap-3">
          <ComicButton variant="primary" size="lg" :loading="testLoading" @click="startTest">开始今日测试</ComicButton>
          <ComicButton variant="light" size="lg" @click="router.push('/')">返回概览</ComicButton>
        </div>
      </ComicPanel>
    </div>

    <div v-else-if="!current" class="py-10 text-center font-black text-[#1a1a1a]">
      今日暂无学习任务，去休息一下吧 ~
    </div>

    <div v-else class="space-y-4">
      <div class="flex items-center justify-between">
        <ComicBadge variant="secondary">{{ progressText }}</ComicBadge>
        <div class="font-bold text-[#1a1a1a]">词库: {{ currentBookName }} · 复习 {{ stats.review_count }} · 新词 {{ stats.new_count }}</div>
      </div>

      <ComicPanel class="mx-auto max-w-3xl">
        <div class="text-center">
          <div class="font-black text-5xl lowercase tracking-wide text-[#1a1a1a] md:text-7xl">{{ current.word }}</div>
          <div class="mt-3 font-bold text-lg text-[#1a1a1a]/70">{{ current.phonetic || '' }}</div>

          <div v-if="current.is_new" class="mt-8 space-y-3">
            <div class="font-black text-xl text-[#1a1a1a] md:text-2xl">{{ current.meaning_zh || '-' }}</div>
            <div class="font-bold text-[#1a1a1a]/60">{{ current.example || '' }}</div>
          </div>

          <div v-else class="mt-8">
            <div v-if="!showMeaning">
              <ComicButton variant="secondary" size="lg" @click="revealMeaning">显示释义</ComicButton>
            </div>
            <div v-else class="space-y-3">
              <div class="font-black text-xl text-[#1a1a1a] md:text-2xl">{{ current.meaning_zh || '-' }}</div>
              <div class="font-bold text-[#1a1a1a]/60">{{ current.example || '' }}</div>
            </div>
          </div>
        </div>
      </ComicPanel>

      <div class="flex flex-wrap justify-center gap-4">
        <ComicButton variant="success" size="lg" @click="grade('know')">认识</ComicButton>
        <ComicButton variant="warning" size="lg" @click="grade('vague')">模糊</ComicButton>
        <ComicButton variant="danger" size="lg" @click="grade('forget')">不认识</ComicButton>
      </div>
    </div>
  </div>
</template>

