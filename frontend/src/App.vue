<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from './stores/app.js'
import request from './api/request.js'
import { ElMessage } from 'element-plus'

const route = useRoute()
const store = useAppStore()
const isCollapse = ref(false)
const settingsVisible = ref(false)
const configForm = ref({
  llm_base_url: '',
  llm_api_key: '',
  llm_model: 'gpt-3.5-turbo',
})

const menus = [
  { index: '/', title: '概览', icon: 'HomeFilled' },
  { index: '/review', title: '今日复习', icon: 'Reading' },
  { index: '/practice', title: '练习', icon: 'EditPen' },
  { index: '/vocab', title: '词库', icon: 'Collection' },
  { index: '/focus', title: '专注', icon: 'Timer' },
  { index: '/tasks', title: '任务', icon: 'List' },
  { index: '/calendar', title: '日历', icon: 'Calendar' },
  { index: '/chat', title: 'AI 答疑', icon: 'ChatDotRound' },
]

onMounted(() => {
  store.loadAiConfig()
})

async function openSettings() {
  await store.loadAiConfig()
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
    ElMessage.success('配置已保存')
    settingsVisible.value = false
  } catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="200px" class="app-aside">
      <div class="logo">
        <el-icon size="24"><Headset /></el-icon>
        <span>AI 学习助手</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="app-menu"
        background-color="#f7f8fc"
        text-color="#333"
        active-text-color="#0f766e"
      >
        <el-menu-item v-for="m in menus" :key="m.index" :index="m.index">
          <el-icon>
            <component :is="m.icon" />
          </el-icon>
          <template #title>{{ m.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div style="flex: 1;"></div>
        <el-button text @click="openSettings">
          <el-icon><Setting /></el-icon>
          <span style="margin-left: 4px;">设置</span>
        </el-button>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <el-drawer v-model="settingsVisible" title="AI 配置" size="360px">
      <el-form label-position="top">
        <el-form-item label="API Base URL">
          <el-input v-model="configForm.llm_base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="configForm.llm_api_key" type="password" placeholder="仅修改时填写，不会回显" />
          <div style="font-size: 12px; color: #888; margin-top: 4px;">留空则保留之前的 API Key</div>
        </el-form-item>
        <el-form-item label="Model">
          <el-input v-model="configForm.llm_model" placeholder="gpt-3.5-turbo" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings" style="width: 100%;">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100vh;
}
.app-aside {
  background: #f7f8fc;
  border-right: 1px solid #e5e7ef;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  font-weight: 600;
  color: #0f766e;
}
.app-menu {
  border-right: none;
}
.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  background: #ffffff;
  border-bottom: 1px solid #e5e7ef;
  padding: 0 20px;
}
.app-main {
  background: #ffffff;
  padding: 20px;
  overflow-y: auto;
}
</style>
