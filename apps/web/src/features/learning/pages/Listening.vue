<script setup>
import { computed, ref } from 'vue'
import request from '../../../api/request.js'
import { ElMessage } from 'element-plus'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

const mode = ref('listen_passage')
const count = ref(3)
const rate = ref(1.0)
const questions = ref([])
const sessionId = ref(null)
const result = ref(null)
const loading = ref(false)
const speakingIndex = ref(-1)

const passageGroups = computed(() => {
  const groups = new Map()
  for (const q of questions.value) {
    const key = Number(q.passage_index || 0)
    if (!key) continue
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(q)
  }
  return [...groups.entries()].map(([passageIndex, items]) => ({ passageIndex, items }))
})

function canSpeak() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

function speakText(text, index) {
  if (!canSpeak()) {
    ElMessage.error('Speech synthesis is not supported in this browser')
    return
  }
  if (!text) return

  window.speechSynthesis.cancel()
  const utter = new SpeechSynthesisUtterance(text)
  utter.lang = 'en-US'
  utter.rate = Number(rate.value) || 1
  utter.onstart = () => {
    speakingIndex.value = index
  }
  utter.onend = () => {
    speakingIndex.value = -1
  }
  utter.onerror = () => {
    speakingIndex.value = -1
    ElMessage.error('Audio playback failed')
  }
  window.speechSynthesis.speak(utter)
}

function speakQuestion(question, index) {
  speakText(question.listen_text || question.correct_answer || '', index)
}

function speakPassage(group) {
  const head = group?.items?.[0]
  if (!head) return
  speakText(head.listen_text || '', group.passageIndex + 1000)
}

async function generate() {
  loading.value = true
  try {
    const { data } = await request.post('/api/listening/generate', { mode: mode.value, count: count.value })
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
  const { data } = await request.post('/api/listening/submit', {
    session_id: sessionId.value,
    answers,
  })
  result.value = data.data
  ElMessage.success(`Correct ${result.value.correct_count}/${result.value.total}`)
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">Listening Training</h2>
      <ComicBadge variant="secondary">LISTEN</ComicBadge>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <el-select v-model="mode" class="w-56">
        <el-option label="L1 Listen MCQ" value="listen_mcq" />
        <el-option label="L1 Listen Fill" value="listen_fill" />
        <el-option label="L3 Passage (Main+Detail+Inference)" value="listen_passage" />
      </el-select>
      <el-input-number v-model="count" :min="1" :max="mode === 'listen_passage' ? 10 : 50" class="w-32" />
      <el-select v-model="rate" class="w-32">
        <el-option :value="0.85" label="0.85x" />
        <el-option :value="1.0" label="1.0x" />
        <el-option :value="1.15" label="1.15x" />
      </el-select>
      <ComicButton variant="primary" :loading="loading" @click="generate">Generate</ComicButton>
    </div>

    <div v-if="mode === 'listen_passage' && passageGroups.length" class="space-y-4">
      <ComicCard v-for="group in passageGroups" :key="group.passageIndex">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div class="font-black text-lg text-[#1a1a1a]">Passage {{ group.passageIndex }}</div>
          <ComicButton
            variant="light"
            size="sm"
            :loading="speakingIndex === group.passageIndex + 1000"
            @click="speakPassage(group)"
          >
            Play Passage
          </ComicButton>
        </div>

        <div v-for="(q, innerIdx) in group.items" :key="q.index" class="mb-4 last:mb-0">
          <div class="mb-2 font-black text-base text-[#1a1a1a]">Q{{ q.index + 1 }}. {{ q.prompt }}</div>
          <div class="flex flex-wrap gap-3">
            <label
              v-for="c in q.choices" :key="c"
              class="flex cursor-pointer items-center gap-2 rounded-lg border-4 border-[#1a1a1a] bg-white px-4 py-2 font-bold shadow-[3px_3px_0px_0px_rgba(26,26,26,1)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]"
              :class="{ 'bg-[#ffbe0b]': q.user_answer === c }"
            >
              <input v-model="q.user_answer" type="radio" :name="`p-${group.passageIndex}-q-${innerIdx}`" :value="c" class="h-4 w-4 accent-[#1a1a1a]">
              <span>{{ c }}</span>
            </label>
          </div>
        </div>
      </ComicCard>

      <div class="flex flex-wrap gap-3">
        <ComicButton variant="primary" size="lg" @click="submit">Submit</ComicButton>
      </div>
    </div>

    <div v-else-if="questions.length" class="space-y-4">
      <ComicCard v-for="(q, idx) in questions" :key="idx">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div class="font-black text-lg text-[#1a1a1a]">Q{{ idx + 1 }}. {{ q.prompt }}</div>
          <ComicButton
            variant="light"
            size="sm"
            :loading="speakingIndex === idx"
            @click="speakQuestion(q, idx)"
          >
            Play
          </ComicButton>
        </div>
        <div v-if="q.type === 'listen_fill'">
          <input v-model="q.user_answer" placeholder="Type the word you heard" class="w-full max-w-sm rounded-lg border-4 border-[#1a1a1a] px-4 py-2 font-bold shadow-[3px_3px_0px_0px_rgba(26,26,26,1)] focus:shadow-[4px_4px_0px_0px_rgba(26,26,26,1)] focus:outline-none">
        </div>
        <div v-else class="flex flex-wrap gap-3">
          <label
            v-for="c in q.choices" :key="c"
            class="flex cursor-pointer items-center gap-2 rounded-lg border-4 border-[#1a1a1a] bg-white px-4 py-2 font-bold shadow-[3px_3px_0px_0px_rgba(26,26,26,1)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]"
            :class="{ 'bg-[#ffbe0b]': q.user_answer === c }"
          >
            <input v-model="q.user_answer" type="radio" :name="`q-${idx}`" :value="c" class="h-4 w-4 accent-[#1a1a1a]">
            <span>{{ c }}</span>
          </label>
        </div>
      </ComicCard>

      <div class="flex flex-wrap gap-3">
        <ComicButton variant="primary" size="lg" @click="submit">Submit</ComicButton>
      </div>
    </div>

    <div v-if="result" class="rounded-lg border-4 border-[#1a1a1a] bg-[#fffef0] p-4 font-bold shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]">
      Correct {{ result.correct_count }}/{{ result.total }}, Wrong {{ result.wrong_count }}
    </div>
  </div>
</template>
