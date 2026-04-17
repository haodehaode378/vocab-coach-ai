<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import request from '../api/request.js'
import ComicCard from '../components/comic/ComicCard.vue'
import ComicBadge from '../components/comic/ComicBadge.vue'

use([CanvasRenderer, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const progress = ref({ total: 0, new: 0, learning: 0, mastered: 0, familiar: 0, mastery_distribution: {} })
const progressError = ref('')

onMounted(async () => {
  progressError.value = ''
  try {
    const { data } = await request.get('/api/study/stats/progress')
    progress.value = {
      ...progress.value,
      ...(data?.data || {}),
    }
  } catch (e) {
    progressError.value = '学习进度加载失败'
  }
})

function safeNumber(value) {
  const num = Number(value)
  return Number.isFinite(num) ? num : 0
}

const statusData = computed(() => {
  const rows = [
    { value: safeNumber(progress.value.new), name: '未学习', itemStyle: { color: '#c0c4cc' } },
    { value: safeNumber(progress.value.learning), name: '学习中', itemStyle: { color: '#e6a23c' } },
    { value: safeNumber(progress.value.mastered), name: '已掌握', itemStyle: { color: '#67c23a' } },
    { value: safeNumber(progress.value.familiar), name: '熟知', itemStyle: { color: '#0f766e' } },
  ]
  const total = rows.reduce((sum, item) => sum + item.value, 0)
  if (total <= 0) {
    return [{ value: 1, name: '暂无数据', itemStyle: { color: '#dcdfe6' } }]
  }
  return rows
})

const masteryRangeOrder = ['0-20', '21-40', '41-60', '61-80', '81-100']
const masteryEntries = computed(() => {
  const source = progress.value.mastery_distribution || {}
  return masteryRangeOrder.map(key => ({
    key,
    value: safeNumber(source[key]),
  }))
})

const statusOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 12 } },
  series: [
    {
      name: '单词状态',
      type: 'pie',
      radius: ['30%', '55%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c}' },
      data: statusData.value,
    },
  ],
}))

const masteryOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 16, right: 16, top: 24, bottom: 24, containLabel: true },
  xAxis: { type: 'category', data: masteryEntries.value.map(i => i.key) },
  yAxis: { type: 'value', min: 0, minInterval: 1 },
  series: [
    {
      data: masteryEntries.value.map(i => i.value),
      type: 'bar',
      itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
      barWidth: '50%',
    },
  ],
}))
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">学习进度</h2>
      <ComicBadge variant="success">WOW!</ComicBadge>
    </div>

    <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#1a1a1a]">{{ progress.total }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">总词量</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#3a86ff]">{{ progress.new }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">未学习</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#ffbe0b]">{{ progress.learning }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">学习中</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#06ffa5]">{{ progress.mastered }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">已掌握</div>
      </ComicCard>
      <ComicCard hoverable>
        <div class="text-3xl font-black text-[#ff006e]">{{ progress.familiar }}</div>
        <div class="text-sm font-bold text-[#1a1a1a]/80">熟知</div>
      </ComicCard>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <ComicCard>
        <template #header>
          <span class="font-black text-lg uppercase tracking-wide">单词状态分布</span>
        </template>
        <div v-if="progressError" class="mb-2 text-xs font-bold text-red-600">{{ progressError }}</div>
        <div class="w-full overflow-hidden" style="height: 288px;">
          <v-chart :option="statusOption" class="size-full" style="height: 288px; width: 100%;" />
        </div>
      </ComicCard>
      <ComicCard>
        <template #header>
          <span class="font-black text-lg uppercase tracking-wide">熟练度分布</span>
        </template>
        <div v-if="progressError" class="mb-2 text-xs font-bold text-red-600">{{ progressError }}</div>
        <div class="w-full overflow-hidden" style="height: 288px;">
          <v-chart :option="masteryOption" class="size-full" style="height: 288px; width: 100%;" />
        </div>
      </ComicCard>
    </div>
  </div>
</template>
