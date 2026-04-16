<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request.js'
import { ElMessage } from 'element-plus'

const keyword = ref('')
const vocab = ref({ total: 0, items: [], page: 1, page_size: 20 })
const bookSelect = ref('all')
const bookOptions = [
  { label: '全部导入', value: 'all' },
  { label: '四级单词 (CET4)', value: 'CET4luan_2.json' },
  { label: '六级单词 (CET6)', value: 'CET6_1.json' },
]

onMounted(() => loadVocab())

async function loadVocab(page = 1) {
  const { data } = await request.get(`/api/vocab/list?keyword=${encodeURIComponent(keyword.value)}&page=${page}&page_size=${vocab.value.page_size}`)
  vocab.value = data.data
}

async function importWords() {
  let files = []
  if (bookSelect.value === 'all') {
    files = ['CET4luan_2.json', 'CET6_1.json']
  } else {
    files = [bookSelect.value]
  }
  await request.post('/api/vocab/import-json-files', { files })
  ElMessage.success('导入成功')
  await loadVocab()
}
</script>

<template>
  <div>
    <h2>词库浏览</h2>
    <div style="display: flex; gap: 10px; margin: 16px 0; flex-wrap: wrap; align-items: center;">
      <el-input v-model="keyword" placeholder="搜索单词" style="max-width: 200px;" @keyup.enter="loadVocab(1)" />
      <el-button @click="loadVocab(1)">搜索</el-button>
      <el-select v-model="bookSelect" style="width: 160px;">
        <el-option v-for="opt in bookOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <el-button type="primary" @click="importWords">导入词库</el-button>
    </div>

    <el-row :gutter="12">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in vocab.items" :key="item.id" style="margin-bottom: 12px;">
        <el-card shadow="hover">
          <div style="font-size: 18px; font-weight: 600;">{{ item.word }}</div>
          <div style="color: #6b7280; font-size: 13px;">{{ item.phonetic || '' }}</div>
          <div style="margin-top: 8px; color: #333;">{{ item.meaning_zh || '-' }}</div>
          <div style="margin-top: 6px; color: #888; font-size: 12px;">{{ item.tags || '-' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-pagination
      v-if="vocab.total > 0"
      background
      layout="prev, pager, next"
      :total="vocab.total"
      :page-size="vocab.page_size"
      :current-page="vocab.page"
      @current-change="loadVocab"
      style="margin-top: 16px;"
    />
  </div>
</template>
