<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '../api/request.js'
import { ElMessage } from 'element-plus'

const reviewItems = ref([])
const currentIndex = ref(0)
const showAnswer = ref(false)
const loading = ref(false)

onMounted(loadReview)

async function loadReview() {
  loading.value = true
  const { data } = await request.get('/api/review/today?limit=50')
  reviewItems.value = data.data
  currentIndex.value = 0
  showAnswer.value = false
  loading.value = false
}

const currentItem = computed(() => reviewItems.value[currentIndex.value])

async function grade(g) {
  if (!currentItem.value) return
  await request.post('/api/review/grade', {
    vocab_item_id: currentItem.value.id,
    grade: g,
  })
  ElMessage.success(`已评分：${g}`)
  showAnswer.value = false
  if (currentIndex.value < reviewItems.value.length - 1) {
    currentIndex.value++
  } else {
    await loadReview()
  }
}
</script>

<template>
  <div>
    <h2>今日复习</h2>
    <p v-if="loading" style="color: #6b7280;">加载中...</p>
    <div v-else-if="reviewItems.length === 0" class="hint">暂无到期单词，休息一下~</div>
    <div v-else>
      <el-card style="max-width: 720px; margin-top: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="color: #6b7280;">{{ currentIndex + 1 }} / {{ reviewItems.length }}</span>
          <el-button text @click="showAnswer = !showAnswer">
            {{ showAnswer ? '隐藏释义' : '显示释义' }}
          </el-button>
        </div>
        <div style="text-align: center; padding: 30px 0;">
          <div style="font-size: 32px; font-weight: 600;">{{ currentItem.word }}</div>
          <div style="color: #6b7280; margin-top: 8px;">{{ currentItem.phonetic || '' }}</div>
          <div v-if="showAnswer" style="margin-top: 20px; font-size: 18px; color: #333;">
            <div>{{ currentItem.meaning_zh || '-' }}</div>
            <div style="margin-top: 8px; color: #888; font-size: 15px;">{{ currentItem.example || '' }}</div>
          </div>
        </div>
        <div style="display: flex; gap: 10px; justify-content: center; margin-top: 10px;">
          <el-button type="danger" @click="grade('again')">Again</el-button>
          <el-button type="warning" @click="grade('hard')">Hard</el-button>
          <el-button type="success" @click="grade('good')">Good</el-button>
          <el-button type="primary" @click="grade('easy')">Easy</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.hint { color: #6b7280; margin-top: 16px; }
</style>
