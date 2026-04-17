<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '../../../api/request.js'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../../../stores/app.js'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicInput from '../../../components/comic/ComicInput.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

const store = useAppStore()
const keyword = ref('')
const vocab = ref({ total: 0, items: [], page: 1, page_size: 20 })
const importBookSelect = ref('all')
const importBookOptions = ref([{ label: '全部导入', value: 'all' }])
const books = ref([])
const totalWords = ref(0)
const currentBookCount = ref(0)

const filterBookTag = computed({
  get: () => store.currentBookTag || '',
  set: (val) => { store.currentBookTag = val },
})

onMounted(async () => {
  await loadImportBooks()
  await loadBooks()
  await loadVocab()
})

async function loadImportBooks() {
  try {
    const { data } = await request.get('/api/system/books')
    const files = data.data || []
    importBookOptions.value = [
      { label: '全部导入', value: 'all' },
      ...files.map((f) => ({ label: f, value: `data/${f}` })),
    ]
  } catch (e) {}
}

async function loadBooks() {
  try {
    const { data } = await request.get('/api/study/books')
    books.value = data.data.books || []
    store.currentBookTag = data.data.current_book_tag || ''
    totalWords.value = data.data.total_words || 0
    currentBookCount.value = data.data.current_book_count || 0
  } catch (e) {}
}

async function loadVocab(page = 1) {
  let url = `/api/vocab/list?keyword=${encodeURIComponent(keyword.value)}&page=${page}&page_size=${vocab.value.page_size}`
  if (filterBookTag.value) {
    url += `&book_tag=${encodeURIComponent(filterBookTag.value)}`
  }
  const { data } = await request.get(url)
  vocab.value = data.data
}

async function importWords() {
  let files = []
  if (importBookSelect.value === 'all') {
    files = importBookOptions.value
      .filter((opt) => opt.value !== 'all')
      .map((opt) => opt.value)
  } else {
    files = [importBookSelect.value]
  }
  if (!files.length) {
    ElMessage.warning('未检测到可导入词库文件')
    return
  }
  await request.post('/api/vocab/import-json-files', { files })
  ElMessage.success('导入成功')
  await loadBooks()
  await loadVocab()
}

async function saveCurrentBook() {
  try {
    await request.post('/api/study/current-book', {
      current_book_tag: store.currentBookTag || null,
    })
    await loadBooks()
    await loadVocab(1)
    ElMessage.success('当前词库已更新')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">词库浏览</h2>
      <ComicBadge variant="secondary">BOOM!</ComicBadge>
      <ComicBadge variant="dark">总词条 {{ totalWords }}</ComicBadge>
      <ComicBadge v-if="store.currentBookTag" variant="warning">当前词库 {{ currentBookCount }}</ComicBadge>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <ComicInput v-model="keyword" placeholder="搜索单词" class="w-48" @enter="loadVocab(1)" />
      <ComicButton variant="light" @click="loadVocab(1)">搜索</ComicButton>
      <el-select v-model="filterBookTag" clearable placeholder="全部词库" class="w-44" @change="loadVocab(1)">
        <el-option
          v-for="b in books"
          :key="b.tag"
          :label="`${b.tag} (${b.count}词)`"
          :value="b.tag"
        />
      </el-select>
      <ComicButton variant="primary" @click="saveCurrentBook">设为当前词库</ComicButton>
      <div class="flex-1"></div>
      <el-select v-model="importBookSelect" class="w-40">
        <el-option v-for="opt in importBookOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <ComicButton variant="warning" @click="importWords">导入词库</ComicButton>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <ComicCard v-for="item in vocab.items" :key="item.id" hoverable>
        <div class="flex items-start justify-between">
          <div class="font-black text-xl text-[#1a1a1a]">{{ item.word }}</div>
          <ComicBadge v-if="item.tags" variant="dark" class="text-xs">{{ item.tags }}</ComicBadge>
        </div>
        <div class="mt-1 font-bold text-sm text-[#1a1a1a]/60">{{ item.phonetic || '' }}</div>
        <div class="mt-3 font-bold text-[#1a1a1a]">{{ item.meaning_zh || '-' }}</div>
      </ComicCard>
    </div>

    <el-pagination
      v-if="vocab.total > 0"
      background
      layout="prev, pager, next"
      :total="vocab.total"
      :page-size="vocab.page_size"
      :current-page="vocab.page"
      @current-change="loadVocab"
      class="mt-4"
    />
  </div>
</template>

