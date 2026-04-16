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

onMounted(async () => {
  const { data } = await request.get('/api/study/stats/progress')
  progress.value = data.data
})

const statusOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: '0%' },
  series: [
    {
      name: '单词状态',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c}' },
      data: [
        { value: progress.value.new, name: '未学习', itemStyle: { color: '#c0c4cc' } },
        { value: progress.value.learning, name: '学习中', itemStyle: { color: '#e6a23c' } },
        { value: progress.value.mastered, name: '已掌握', itemStyle: { color: '#67c23a' } },
        { value: progress.value.familiar, name: '熟知', itemStyle: { color: '#0f766e' } },
      ],
    },
  ],
}))

const masteryOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  xAxis: { type: 'category', data: Object.keys(progress.value.mastery_distribution || {}) },
  yAxis: { type: 'value' },
  series: [
    {
      data: Object.values(progress.value.mastery_distribution || {}),
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
        <v-chart :option="statusOption" class="h-72" />
      </ComicCard>
      <ComicCard>
        <template #header>
          <span class="font-black text-lg uppercase tracking-wide">熟练度分布</span>
        </template>
        <v-chart :option="masteryOption" class="h-72" />
      </ComicCard>
    </div>
  </div>
</template>
