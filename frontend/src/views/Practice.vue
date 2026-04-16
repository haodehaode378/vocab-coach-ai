<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request.js'
import { ElMessage } from 'element-plus'

const mode = ref('mcq')
const count = ref(10)
const questions = ref([])
const sessionId = ref(null)
const result = ref(null)
const loading = ref(false)

async function generate() {
  loading.value = true
  try {
    const { data } = await request.post('/api/practice/generate', { mode: mode.value, count: count.value })
    sessionId.value = data.data.session_id
    questions.value = data.data.questions.map(q => ({ ...q, user_answer: '' }))
    result.value = null
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!sessionId.value) return
  const answers = questions.value.map(q => ({
    vocab_item_id: q.vocab_item_id,
    question_type: q.type,
    user_answer: q.user_answer,
    correct_answer: q.correct_answer,
  }))
  const { data } = await request.post('/api/practice/submit', {
    session_id: sessionId.value,
    answers,
  })
  result.value = data.data
  ElMessage.success(`正确 ${result.value.correct_count}/${result.value.total}`)
}
</script>

<template>
  <div>
    <h2>练习模式</h2>
    <div style="display: flex; gap: 10px; margin: 16px 0; align-items: center;">
      <el-select v-model="mode" style="width: 120px;">
        <el-option label="选择题" value="mcq" />
        <el-option label="拼写题" value="spelling" />
      </el-select>
      <el-input-number v-model="count" :min="1" :max="50" style="width: 120px;" />
      <el-button type="primary" @click="generate" :loading="loading">生成题目</el-button>
    </div>

    <div v-if="questions.length">
      <el-card v-for="(q, idx) in questions" :key="idx" style="margin-bottom: 12px; max-width: 720px;">
        <div style="font-weight: 600; margin-bottom: 10px;">Q{{ idx + 1 }}. {{ q.prompt }}</div>
        <div v-if="q.type === 'mcq'">
          <el-radio-group v-model="q.user_answer">
            <el-radio v-for="c in q.choices" :key="c" :label="c">{{ c }}</el-radio>
          </el-radio-group>
        </div>
        <div v-else>
          <el-input v-model="q.user_answer" placeholder="输入拼写" style="max-width: 300px;" />
        </div>
      </el-card>
      <el-button type="primary" @click="submit" style="margin-top: 8px;">提交练习</el-button>
    </div>

    <el-alert v-if="result" :title="`正确 ${result.correct_count}/${result.total}，错误 ${result.wrong_count}`" type="info" show-icon style="margin-top: 16px; max-width: 720px;" />
  </div>
</template>
