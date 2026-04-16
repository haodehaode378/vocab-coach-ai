<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '../api/request.js'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const queue = ref([])
const currentIndex = ref(0)
const showMeaning = ref(false)
const loading = ref(false)
const finished = ref(false)
const stats = ref({ review_count: 0, new_count: 0 })
const testLoading = ref(false)

onMounted(loadQueue)

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
  <div>
    <h2>今日学习</h2>
    <p v-if="loading" style="color: #6b7280; margin-top: 12px;">加载中...</p>
    <div v-else-if="finished" style="text-align: center; margin-top: 40px;">
      <el-result icon="success" title="今日学习完成" sub-title="继续保持，积少成多">
        <template #extra>
          <el-button type="primary" :loading="testLoading" @click="startTest">开始今日测试</el-button>
          <el-button @click="router.push('/')">返回概览</el-button>
        </template>
      </el-result>
    </div>
    <div v-else-if="!current" style="color: #6b7280; margin-top: 20px;">
      今日暂无学习任务，去休息一下吧 ~
    </div>
    <div v-else>
      <div style="display: flex; justify-content: space-between; align-items: center; margin: 12px 0; color: #6b7280;">
        <span>{{ progressText }}</span>
        <span>复习 {{ stats.review_count }} · 新词 {{ stats.new_count }}</span>
      </div>

      <el-card style="max-width: 720px; min-height: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div>
          <div style="text-align: center; padding-top: 20px;">
            <div style="font-size: 36px; font-weight: 600;">{{ current.word }}</div>
            <div style="color: #6b7280; margin-top: 8px; font-size: 16px;">{{ current.phonetic || '' }}</div>

            <!-- 新词模式：直接展示释义 -->
            <div v-if="current.is_new" style="margin-top: 30px; font-size: 18px; color: #333; line-height: 1.6;">
              <div>{{ current.meaning_zh || '-' }}</div>
              <div style="margin-top: 10px; color: #888; font-size: 15px;">{{ current.example || '' }}</div>
            </div>

            <!-- 复习模式：先隐藏释义 -->
            <div v-else style="margin-top: 30px;">
              <div v-if="!showMeaning">
                <el-button text type="primary" size="large" @click="revealMeaning">显示释义</el-button>
              </div>
              <div v-else style="font-size: 18px; color: #333; line-height: 1.6;">
                <div>{{ current.meaning_zh || '-' }}</div>
                <div style="margin-top: 10px; color: #888; font-size: 15px;">{{ current.example || '' }}</div>
              </div>
            </div>
          </div>
        </div>

        <div style="margin-top: 30px; display: flex; gap: 12px; justify-content: center;">
          <el-button size="large" type="success" @click="grade('know')" style="min-width: 100px;">认识</el-button>
          <el-button size="large" type="warning" @click="grade('vague')" style="min-width: 100px;">模糊</el-button>
          <el-button size="large" type="danger" @click="grade('forget')" style="min-width: 100px;">不认识</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>
