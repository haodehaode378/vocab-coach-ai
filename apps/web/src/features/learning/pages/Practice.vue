<script setup>
import { ref, onMounted } from 'vue'
import request from '../../../api/request.js'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

const route = useRoute()
const router = useRouter()
const isDailyTest = ref(false)

const mode = ref('mcq')
const count = ref(10)
const questions = ref([])
const sessionId = ref(null)
const result = ref(null)
const loading = ref(false)

function hydrateQuestion(q) {
  return {
    ...q,
    user_answer: '',
    submitting: false,
    submitted: false,
    is_correct: null,
    correct_answer_feedback: '',
    explanation_feedback: '',
  }
}

onMounted(() => {
  if (route.query.source === 'daily_test') {
    isDailyTest.value = true
    const raw = localStorage.getItem('daily_test_session')
    if (raw) {
      try {
        const payload = JSON.parse(raw)
        sessionId.value = payload.session_id
        questions.value = payload.questions.map(hydrateQuestion)
        result.value = null
        localStorage.removeItem('daily_test_session')
      } catch {
        ElMessage.error('测试数据加载失败')
      }
    }
  }
})

async function generate() {
  loading.value = true
  try {
    const { data } = await request.post('/api/practice/generate', { mode: mode.value, count: count.value })
    sessionId.value = data.data.session_id
    questions.value = data.data.questions.map(hydrateQuestion)
    result.value = null
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function submitOne(q) {
  if (!sessionId.value) return
  if (!q.user_answer?.trim()) {
    ElMessage.warning('请先作答再提交本题')
    return
  }

  q.submitting = true
  try {
    const { data } = await request.post('/api/practice/submit-one', {
      session_id: sessionId.value,
      answer: {
        vocab_item_id: q.vocab_item_id,
        question_type: q.type,
        user_answer: q.user_answer,
        correct_answer: q.correct_answer,
      },
    })
    q.submitted = true
    q.is_correct = data.data.is_correct
    q.correct_answer_feedback = data.data.correct_answer
    q.explanation_feedback = data.data.explanation || ''
    result.value = {
      total: data.data.total_questions,
      answered_count: data.data.answered_count,
      correct_count: data.data.correct_count,
      wrong_count: data.data.wrong_count,
    }
    ElMessage.success(q.is_correct ? '本题正确' : '本题错误')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally {
    q.submitting = false
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
  const detailMap = new Map((data.data.wrong_details || []).map(d => [`${d.vocab_item_id}::${d.question_type}`, d]))
  questions.value.forEach((q) => {
    q.submitted = true
    q.is_correct = String(q.user_answer || '').trim().toLowerCase() === String(q.correct_answer || '').trim().toLowerCase()
    const key = `${q.vocab_item_id}::${q.type}`
    const detail = detailMap.get(key)
    if (detail) {
      q.correct_answer_feedback = detail.correct_answer
      q.explanation_feedback = detail.explanation || ''
    } else {
      q.correct_answer_feedback = q.correct_answer
      q.explanation_feedback = ''
    }
  })
  ElMessage.success(`正确 ${result.value.correct_count}/${result.value.answered_count || result.value.total}`)
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">{{ isDailyTest ? '今日测试' : '练习模式' }}</h2>
      <ComicBadge variant="primary">POW!</ComicBadge>
    </div>

    <div v-if="!isDailyTest" class="flex flex-wrap items-center gap-3">
      <el-select v-model="mode" class="w-32">
        <el-option label="选择题" value="mcq" />
        <el-option label="拼写题" value="spelling" />
        <el-option label="段落推断词" value="context_infer" />
      </el-select>
      <el-input-number v-model="count" :min="1" :max="50" class="w-32" />
      <ComicButton variant="primary" :loading="loading" @click="generate">生成题目</ComicButton>
    </div>

    <div v-if="questions.length" class="space-y-4">
      <ComicCard v-for="(q, idx) in questions" :key="idx">
        <div class="mb-3 font-black text-lg text-[#1a1a1a]">Q{{ idx + 1 }}. {{ q.prompt }}</div>
        <div v-if="q.type === 'mcq' || q.type === 'context_infer_mcq'" class="flex flex-wrap gap-3">
          <label
            v-for="c in q.choices" :key="c"
            class="flex cursor-pointer items-center gap-2 rounded-lg border-4 border-[#1a1a1a] bg-white px-4 py-2 font-bold shadow-[3px_3px_0px_0px_rgba(26,26,26,1)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]"
            :class="{ 'bg-[#ffbe0b]': q.user_answer === c }"
          >
            <input v-model="q.user_answer" type="radio" :name="`q-${idx}`" :value="c" class="h-4 w-4 accent-[#1a1a1a]">
            <span>{{ c }}</span>
          </label>
        </div>
        <div v-else>
          <input v-model="q.user_answer" placeholder="输入拼写" class="w-full max-w-sm rounded-lg border-4 border-[#1a1a1a] px-4 py-2 font-bold shadow-[3px_3px_0px_0px_rgba(26,26,26,1)] focus:shadow-[4px_4px_0px_0px_rgba(26,26,26,1)] focus:outline-none">
        </div>
        <div class="mt-3 flex items-center gap-3">
          <ComicButton variant="secondary" size="sm" :loading="q.submitting" @click="submitOne(q)">提交本题</ComicButton>
          <span v-if="q.submitted" class="font-bold" :class="q.is_correct ? 'text-[#2f9e44]' : 'text-[#d00000]'">
            {{ q.is_correct ? '本题正确' : '本题错误' }}
          </span>
        </div>
        <div v-if="q.submitted && q.is_correct === false" class="mt-2 rounded-lg border-2 border-[#d00000] bg-[#fff5f5] p-3 text-sm font-bold text-[#1a1a1a]">
          <div>正确答案：{{ q.correct_answer_feedback || q.correct_answer }}</div>
          <div v-if="q.explanation_feedback" class="mt-1">解析：{{ q.explanation_feedback }}</div>
        </div>
      </ComicCard>

      <div class="flex flex-wrap gap-3">
        <ComicButton variant="primary" size="lg" @click="submit">提交{{ isDailyTest ? '测试' : '练习' }}</ComicButton>
        <ComicButton v-if="isDailyTest" variant="light" size="lg" @click="router.push('/')">返回概览</ComicButton>
      </div>
    </div>

    <div v-else-if="isDailyTest" class="py-8 text-center font-black text-[#1a1a1a]">
      暂无测试题目，先去完成今日学习吧 ~
    </div>

    <div v-if="result" class="rounded-lg border-4 border-[#1a1a1a] bg-[#fffef0] p-4 font-bold shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]">
      已提交 {{ result.answered_count || result.total }}/{{ result.total }}，正确 {{ result.correct_count }}，错误 {{ result.wrong_count }}
    </div>
  </div>
</template>

