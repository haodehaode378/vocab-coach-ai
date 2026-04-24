<script setup>
import { ref, nextTick, onMounted } from 'vue'
import request from '../../../api/request.js'
import { useAppStore } from '../../../stores/app.js'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicInput from '../../../components/comic/ComicInput.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

const store = useAppStore()
const messages = ref([])
const input = ref('')
const loading = ref(false)
const chatBox = ref(null)

const shortcuts = [
  '解释单词差异',
  '生成小测',
  '学习建议',
  '激励我',
]

function getWelcomeMessage() {
  return { role: 'assistant', content: '你好！我是你的 AI 英语背词助手，有什么可以帮你的吗？' }
}

onMounted(async () => {
  await loadHistory()
})

async function loadHistory() {
  try {
    const { data } = await request.get('/api/ai/chat/history?limit=80')
    const history = (data.data.messages || []).map(m => ({ role: m.role, content: m.content }))
    messages.value = history.length ? history : [getWelcomeMessage()]
  } catch (e) {
    messages.value = [getWelcomeMessage()]
  }
  scrollToBottom()
}

async function clearHistory() {
  try {
    await request.post('/api/ai/chat/clear', {})
    messages.value = [getWelcomeMessage()]
    ElMessage.success('已清空聊天记录')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '清空失败')
  }
}

async function send(text = input.value) {
  if (!text.trim()) return
  const userText = text.trim()
  messages.value.push({ role: 'user', content: userText })
  input.value = ''
  scrollToBottom()
  loading.value = true

  const payload = {
    messages: [{ role: 'user', content: userText }],
    stream: true,
    use_history: true,
    history_limit: 20,
    model: store.llmModel,
    base_url: store.llmBaseUrl || undefined,
    user_email: store.userEmail,
  }

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok || !res.body) {
      throw new Error(`请求失败: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let assistantMessage = ''
    messages.value.push({ role: 'assistant', content: '' })

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data:')) continue
        const dataStr = line.replace(/^data:\s*/, '')
        if (dataStr === '[DONE]') continue
        try {
          const obj = JSON.parse(dataStr)
          assistantMessage += obj.content || ''
          messages.value[messages.value.length - 1].content = assistantMessage
          scrollToBottom()
        } catch (e) {}
      }
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `[请求出错] ${e.message || ''}`.trim() })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
  })
}

function useShortcut(s) {
  send(s)
}

function renderMarkdown(text) {
  const raw = marked.parse(text || '', { breaks: true, gfm: true })
  return DOMPurify.sanitize(raw)
}
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">AI 答疑</h2>
      <ComicBadge variant="secondary">CHAT!</ComicBadge>
      <ComicButton variant="light" size="sm" @click="clearHistory">清空历史</ComicButton>
    </div>

    <ComicCard class="flex flex-1 flex-col overflow-hidden">
      <div ref="chatBox" class="flex-1 overflow-y-auto pr-2">
        <div v-for="(m, idx) in messages" :key="idx" class="mb-4 flex" :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
          <div
            class="markdown-body max-w-[80%] rounded-lg border-4 border-[#1a1a1a] px-4 py-2 font-bold shadow-[4px_4px_0px_0px_rgba(26,26,26,1)] md:max-w-[70%]"
            :class="m.role === 'user' ? 'bg-[#ff006e] text-white' : 'bg-white text-[#1a1a1a]'"
          >
            <div v-html="renderMarkdown(m.content)" />
            <span v-if="m.role === 'assistant' && loading && idx === messages.length - 1" class="typing ml-1">▌</span>
          </div>
        </div>
      </div>
    </ComicCard>

    <div class="flex flex-wrap gap-2">
      <ComicButton v-for="s in shortcuts" :key="s" variant="light" size="sm" @click="useShortcut(s)">{{ s }}</ComicButton>
    </div>

    <div class="flex gap-3">
      <ComicInput v-model="input" placeholder="输入问题..." class="flex-1" @enter="send()" />
      <ComicButton variant="primary" size="lg" :loading="loading" @click="send()">发送</ComicButton>
    </div>
  </div>
</template>

<style scoped>
.markdown-body :deep(p) {
  margin: 0.25rem 0;
}
.markdown-body :deep(pre) {
  overflow-x: auto;
  border-radius: 0.5rem;
  border: 2px solid #1a1a1a;
  padding: 0.5rem;
  background: #fffef0;
  color: #1a1a1a;
}
.markdown-body :deep(code) {
  border-radius: 0.25rem;
  background: rgba(26, 26, 26, 0.08);
  padding: 0.1rem 0.25rem;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.25rem 0;
  padding-left: 1.25rem;
}
.typing {
  animation: blink 1s step-start infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
</style>
