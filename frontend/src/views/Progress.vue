<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import request from '../api/request.js'

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
  <div>
    <h2>学习进度</h2>
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ progress.total }}</div>
          <div style="color: #6b7280; font-size: 13px;">总词量</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ progress.new }}</div>
          <div style="color: #6b7280; font-size: 13px;">未学习</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ progress.learning }}</div>
          <div style="color: #6b7280; font-size: 13px;">学习中</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ progress.mastered }}</div>
          <div style="color: #6b7280; font-size: 13px;">已掌握</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ progress.familiar }}</div>
          <div style="color: #6b7280; font-size: 13px;">熟知</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>单词状态分布</template>
          <v-chart :option="statusOption" style="height: 300px;" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>熟练度分布</template>
          <v-chart :option="masteryOption" style="height: 300px;" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
