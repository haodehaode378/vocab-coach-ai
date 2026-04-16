<script setup>
import { ref, nextTick, onMounted } from 'vue'
import request from '../api/request.js'
import { useAppStore } from '../stores/app.js'

const store = useAppStore()
const messages = ref([
  { role: 'assistant', content: '你好！我是你的 AI 学习助手，有什么可以帮你的吗？' }
])
const input = ref('')
const loading = ref(false)
const chatBox = ref(null)

const shortcuts = [
  '解释单词差异',
  '生成小测',
  '学习建议',
  '激励我',
]

async function send(text = input.value) {
  if (!text.trim()) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  scrollToBottom()
  loading.value = true

  const payload = {
    messages: messages.value.filter(m => m.role === 'user' || m.role === 'assistant').map(m => ({ role: m.role, content: m.content })),
    stream: true,
    model: store.llmModel,
    base_url: store.llmBaseUrl || undefined,
  }

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

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
    messages.value[messages.value.length - 1].content = '[请求出错]'
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
</script>

<template>
  <div>
    <h2>AI 答疑</h2>
    <div style="max-width: 800px; margin-top: 12px;">
      <div ref="chatBox" style="height: 480px; overflow-y: auto; border: 1px solid #e5e7ef; border-radius: 12px; padding: 16px; background: #f9fafb;">
        <div v-for="(m, idx) in messages" :key="idx" style="margin-bottom: 14px; display: flex;" :style="m.role === 'user' ? 'justify-content: flex-end;' : 'justify-content: flex-start;'">
          <div style="max-width: 70%; padding: 10px 14px; border-radius: 14px; line-height: 1.5; white-space: pre-wrap;"
               :style="m.role === 'user' ? 'background: #0f766e; color: #fff;' : 'background: #fff; border: 1px solid #e5e7ef;'">
            {{ m.content }}
            <span v-if="m.role === 'assistant' && loading && idx === messages.length - 1" class="typing">▌</span>
          </div>
        </div>
      </div>

      <div style="margin: 10px 0;">
        <el-space>
          <el-button v-for="s in shortcuts" :key="s" size="small" @click="useShortcut(s)">{{ s }}</el-button>
        </el-space>
      </div>

      <div style="display: flex; gap: 10px;">
        <el-input v-model="input" placeholder="输入问题..." @keyup.enter="send()" />
        <el-button type="primary" @click="send()" :loading="loading">发送</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.typing {
  animation: blink 1s step-start infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
</style>
