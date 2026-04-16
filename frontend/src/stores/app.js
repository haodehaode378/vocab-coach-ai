import { ref } from 'vue'
import { defineStore } from 'pinia'
import request from '../api/request.js'

export const useAppStore = defineStore('app', () => {
  const userEmail = ref(localStorage.getItem('ava_user_email') || 'local@ai-vocab-agent.dev')
  const llmBaseUrl = ref('')
  const llmModel = ref('gpt-3.5-turbo')
  const currentBookTag = ref('')

  async function loadAiConfig() {
    try {
      const { data } = await request.get('/api/system/ai-config')
      llmBaseUrl.value = data.data.base_url || ''
      llmModel.value = data.data.model || 'gpt-3.5-turbo'
    } catch (e) {
      // ignore
    }
  }

  async function loadCurrentBook() {
    try {
      const { data } = await request.get('/api/study/books')
      currentBookTag.value = data.data.current_book_tag || ''
    } catch (e) {
      // ignore
    }
  }

  function saveUserEmail() {
    localStorage.setItem('ava_user_email', userEmail.value)
  }

  return {
    userEmail,
    llmBaseUrl,
    llmModel,
    currentBookTag,
    loadAiConfig,
    loadCurrentBook,
    saveUserEmail,
  }
})
