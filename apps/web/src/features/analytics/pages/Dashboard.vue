<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import request from '../../../api/request.js'
import { useRouter } from 'vue-router'
import { useAppStore } from '../../../stores/app.js'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const store = useAppStore()
const dashboard = ref({
  vocab_count: 0, due_today: 0, today_reviewed: 0,
  today_focus_minutes: 0, today_tasks_completed: 0,
  review_trend: [], focus_trend: []
})
const progress = ref({ total: 0, new: 0, learning: 0, mastered: 0, familiar: 0 })
const dashboardError = ref('')
const progressError = ref('')
const currentBookLabel = computed(() => store.currentBookTag || '全部词库')

onMounted(async () => {
  await store.loadCurrentBook()
  await loadDashboard()
  await loadProgress()
})

async function loadDashboard() {
  dashboardError.value = ''
  try {
    const { data } = await request.get('/api/stats/dashboard')
    dashboard.value = {
      ...dashboard.value,
      ...(data?.data || {}),
    }
  } catch (e) {
    dashboardError.value = '统计数据加载失败'
  }
}

async function loadProgress() {
  try {
    const { data } = await request.get('/api/study/stats/progress')
    progress.value = {
      ...progress.value,
      ...(data?.data || {}),
    }
  } catch (e) {
    progressError.value = '学习进度加载失败'
  }
}

function safeNumber(value) {
  const num = Number(value)
  return Number.isFinite(num) ? num : 0
}

function normalizeTrend(items, valueKey) {
  if (!Array.isArray(items)) return []
  return items.map((item, index) => ({
    date: item?.date || `${index + 1}`,
    value: safeNumber(item?.[valueKey]),
  }))
}

function buildYAxis(maxValue) {
  const safeMax = safeNumber(maxValue)
  return {
    type: 'value',
    min: 0,
    max: safeMax <= 0 ? 5 : Math.ceil(safeMax * 1.2),
    minInterval: 1,
    axisLabel: { margin: 12, formatter: value => `${Math.round(value)}` },
  }
}

const reviewTrend = computed(() => normalizeTrend(dashboard.value.review_trend, 'count'))
const focusTrend = computed(() => normalizeTrend(dashboard.value.focus_trend, 'minutes'))

const reviewChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 64, right: 20, top: 24, bottom: 36, containLabel: true },
  xAxis: { type: 'category', data: reviewTrend.value.map(i => i.date), boundaryGap: false },
  yAxis: buildYAxis(Math.max(...reviewTrend.value.map(i => i.value), 0)),
  series: [{ data: reviewTrend.value.map(i => i.value), type: 'line', smooth: true, name: '复习数' }],
}))

const focusChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 64, right: 20, top: 24, bottom: 36, containLabel: true },
  xAxis: { type: 'category', data: focusTrend.value.map(i => i.date) },
  yAxis: buildYAxis(Math.max(...focusTrend.value.map(i => i.value), 0)),
  series: [{ data: focusTrend.value.map(i => i.value), type: 'bar', name: '专注分钟' }],
}))
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">概览</h2>
      <ComicBadge variant="warning">POW!</ComicBadge>
      <ComicBadge variant="dark">当前词库 {{ currentBookLabel }}</ComicBadge>
    </div>

    <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#ff006e]">{{ dashboard.vocab_count }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">词条总数</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#3a86ff]">{{ dashboard.due_today }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">今日到期</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#06ffa5]">{{ dashboard.today_reviewed }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">今日复习</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#ffbe0b]">{{ dashboard.today_focus_minutes }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">专注分钟</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#fb5607]">{{ dashboard.today_tasks_completed }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">完成任务</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#1a1a1a]">{{ dashboard.due_today }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">待复习</div>
      </ComicCard>
    </div>

    <ComicCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-black text-lg uppercase tracking-wide">学习进度概览</span>
          <ComicBadge variant="success">BAM!</ComicBadge>
        </div>
      </template>
      <div class="flex flex-wrap items-center gap-6">
        <div>
          <div class="text-2xl font-black text-[#ff006e]">{{ progress.total - progress.new }}</div>
          <div class="text-sm font-bold text-[#1a1a1a]/80">已学单词</div>
        </div>
        <div>
          <div class="text-2xl font-black text-[#06ffa5]">{{ progress.mastered }}</div>
          <div class="text-sm font-bold text-[#1a1a1a]/80">已掌握</div>
        </div>
        <div>
          <div class="text-2xl font-black text-[#3a86ff]">{{ progress.familiar }}</div>
          <div class="text-sm font-bold text-[#1a1a1a]/80">熟知</div>
        </div>
        <div class="flex flex-1 justify-end gap-3">
          <ComicButton variant="primary" @click="router.push('/study')">开始学习</ComicButton>
          <ComicButton variant="light" @click="router.push('/progress')">查看进度</ComicButton>
        </div>
      </div>
    </ComicCard>

    <ComicCard>
      <template #header>
        <span class="font-black text-lg uppercase tracking-wide">快捷入口</span>
      </template>
      <div class="flex flex-wrap gap-3">
        <ComicButton variant="primary" @click="router.push('/study')">开始学习</ComicButton>
        <ComicButton variant="secondary" @click="router.push('/practice')">去练习</ComicButton>
        <ComicButton variant="warning" @click="router.push('/focus')">专注计时</ComicButton>
        <ComicButton variant="success" @click="router.push('/tasks')">任务管理</ComicButton>
      </div>
    </ComicCard>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <ComicCard>
        <template #header>
          <span class="font-black text-lg uppercase tracking-wide">近7天复习趋势</span>
        </template>
        <div v-if="dashboardError" class="mb-2 text-xs font-bold text-red-600">{{ dashboardError }}</div>
        <div class="w-full overflow-hidden" style="height: 320px;">
          <v-chart :option="reviewChartOption" class="size-full" style="height: 320px; width: 100%;" />
        </div>
      </ComicCard>
      <ComicCard>
        <template #header>
          <span class="font-black text-lg uppercase tracking-wide">近7天专注趋势</span>
        </template>
        <div v-if="dashboardError" class="mb-2 text-xs font-bold text-red-600">{{ dashboardError }}</div>
        <div class="w-full overflow-hidden" style="height: 320px;">
          <v-chart :option="focusChartOption" class="size-full" style="height: 320px; width: 100%;" />
        </div>
      </ComicCard>
    </div>
    <div v-if="progressError" class="text-xs font-bold text-red-600">{{ progressError }}</div>
  </div>
</template>

