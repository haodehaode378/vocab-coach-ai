<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from './stores/app.js'
import request from './api/request.js'
import { ElMessage } from 'element-plus'
import ComicNav from './components/comic/ComicNav.vue'
import ComicButton from './components/comic/ComicButton.vue'

const route = useRoute()
const store = useAppStore()
const settingsVisible = ref(false)
const configForm = ref({
  llm_base_url: '',
  llm_api_key: '',
  llm_model: 'gpt-3.5-turbo',
})
const books = ref([])
const aiTestLoading = ref(false)
const aiTestResult = ref('')

const menus = [
  { index: '/', title: '概览', icon: 'HomeFilled' },
  { index: '/study', title: '今日学习', icon: 'Reading' },
  { index: '/practice', title: '练习', icon: 'EditPen' },
  { index: '/progress', title: '进度统计', icon: 'DataLine' },
  { index: '/vocab', title: '词库', icon: 'Collection' },
  { index: '/focus', title: '专注', icon: 'Timer' },
  { index: '/tasks', title: '任务', icon: 'List' },
  { index: '/calendar', title: '日历', icon: 'Calendar' },
  { index: '/chat', title: 'AI 答疑', icon: 'ChatDotRound' },
]

const studySettings = ref({ daily_new_words: 20, daily_review_limit: 50 })

onMounted(async () => {
  store.loadAiConfig()
  await loadStudySettings()
  await loadBooks()
})

async function loadBooks() {
  try {
    const { data } = await request.get('/api/study/books')
    books.value = data.data.books || []
    store.currentBookTag = data.data.current_book_tag || ''
  } catch (e) {}
}

async function testAiConnection() {
  aiTestLoading.value = true
  aiTestResult.value = ''
  try {
    const { data } = await request.post('/api/ai/daily-motivation', {
      stats_context: '测试连接',
      base_url: configForm.value.llm_base_url || undefined,
      api_key: configForm.value.llm_api_key.trim() || undefined,
      model: configForm.value.llm_model || undefined,
    })
    const msg = data.data.message
    if (msg && msg.startsWith('[AI 请求出错')) {
      aiTestResult.value = msg
      ElMessage.error(msg)
    } else {
      aiTestResult.value = msg || '连接成功'
      ElMessage.success('连接成功')
    }
  } catch (e) {
    const err = e.response?.data?.detail || e.message || '连接失败'
    aiTestResult.value = err
    ElMessage.error(err)
  } finally {
    aiTestLoading.value = false
  }
}

async function loadStudySettings() {
  try {
    const { data } = await request.get('/api/study/settings')
    studySettings.value = data.data
  } catch (e) {}
}

async function openSettings() {
  await store.loadAiConfig()
  await loadStudySettings()
  await loadBooks()
  configForm.value = {
    llm_base_url: store.llmBaseUrl,
    llm_api_key: '',
    llm_model: store.llmModel,
  }
  settingsVisible.value = true
}

async function saveSettings() {
  const payload = {
    base_url: configForm.value.llm_base_url || null,
    model: configForm.value.llm_model || null,
  }
  if (configForm.value.llm_api_key.trim()) {
    payload.api_key = configForm.value.llm_api_key.trim()
  }
  try {
    await request.post('/api/system/ai-config', payload)
    store.llmBaseUrl = configForm.value.llm_base_url
    store.llmModel = configForm.value.llm_model
    await request.post('/api/study/settings', {
      daily_new_words: studySettings.value.daily_new_words,
      daily_review_limit: studySettings.value.daily_review_limit,
    })
    await request.post('/api/study/current-book', {
      current_book_tag: store.currentBookTag || null,
    })
    ElMessage.success('配置已保存')
    settingsVisible.value = false
  } catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden">
    <ComicNav :menus="menus" />

    <div class="flex flex-1 flex-col overflow-hidden">
      <header class="flex h-16 items-center justify-between border-b-4 border-[#1a1a1a] bg-white px-6">
        <h1 class="font-black text-lg uppercase tracking-wide text-[#1a1a1a] md:text-xl">
          {{ menus.find(m => m.index === route.path)?.title || 'AI 英语背词助手' }}
        </h1>
        <ComicButton variant="dark" size="sm" @click="openSettings">
          <el-icon class="mr-1"><Setting /></el-icon>
          设置
        </ComicButton>
      </header>

      <main class="flex-1 overflow-y-auto p-4 md:p-8">
        <router-view />
      </main>
    </div>

    <el-drawer v-model="settingsVisible" title="设置" size="380px">
      <div class="space-y-6">
        <div>
          <div class="mb-3 font-black text-lg uppercase tracking-wide">学习计划</div>
          <div class="mb-2 font-bold">每日新词量: {{ studySettings.daily_new_words }}</div>
          <el-slider v-model="studySettings.daily_new_words" :min="5" :max="100" :step="5" show-stops />
          <div class="mb-2 mt-4 font-bold">每日复习上限: {{ studySettings.daily_review_limit }}</div>
          <el-slider v-model="studySettings.daily_review_limit" :min="10" :max="300" :step="10" show-stops />
        </div>

        <div>
          <div class="mb-3 font-black text-lg uppercase tracking-wide">当前词库</div>
          <el-select v-model="store.currentBookTag" clearable placeholder="全部词库" class="w-full">
            <el-option
              v-for="b in books"
              :key="b.tag"
              :label="`${b.tag} (${b.count}词)`"
              :value="b.tag"
            />
          </el-select>
          <div class="mt-2 text-xs font-bold text-[#1a1a1a]/70">选择后，学习、练习、统计将仅针对该词库</div>
        </div>

        <div>
          <div class="mb-3 font-black text-lg uppercase tracking-wide">AI 配置</div>
          <div class="mb-3">
            <div class="mb-1 text-sm font-bold">API Base URL</div>
            <el-input v-model="configForm.llm_base_url" placeholder="https://api.openai.com/v1" />
          </div>
          <div class="mb-3">
            <div class="mb-1 text-sm font-bold">API Key</div>
            <el-input v-model="configForm.llm_api_key" type="password" placeholder="仅修改时填写，不会回显" />
            <div class="mt-1 text-xs font-bold text-[#1a1a1a]/70">留空则保留之前的 API Key</div>
          </div>
          <div class="mb-3">
            <div class="mb-1 text-sm font-bold">Model</div>
            <el-input v-model="configForm.llm_model" placeholder="gpt-3.5-turbo" />
          </div>
          <ComicButton variant="light" size="md" class="w-full" :loading="aiTestLoading" @click="testAiConnection">
            测试 AI 连接
          </ComicButton>
          <div v-if="aiTestResult" class="mt-3 rounded-lg border-4 border-[#1a1a1a] p-3 text-sm font-bold"
               :class="aiTestResult.startsWith('[AI 请求出错') || aiTestResult.startsWith('连接失败') ? 'bg-[#fb5607] text-white' : 'bg-[#06ffa5] text-[#1a1a1a]'">
            {{ aiTestResult }}
          </div>
        </div>

        <ComicButton variant="primary" size="lg" class="w-full" @click="saveSettings">
          保存配置
        </ComicButton>
      </div>
    </el-drawer>
  </div>
</template>
