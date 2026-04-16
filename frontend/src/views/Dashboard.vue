<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import request from '../api/request.js'
import { useRouter } from 'vue-router'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const dashboard = ref({
  vocab_count: 0, due_today: 0, today_reviewed: 0,
  today_focus_minutes: 0, today_tasks_completed: 0,
  review_trend: [], focus_trend: []
})
const motivation = ref('')
const loadingMotivation = ref(false)

onMounted(async () => {
  await loadDashboard()
  await loadMotivation()
})

async function loadDashboard() {
  const { data } = await request.get('/api/stats/dashboard')
  dashboard.value = data.data
}

async function loadMotivation() {
  loadingMotivation.value = true
  try {
    const ctx = `今日复习${dashboard.value.today_reviewed}个单词，专注${dashboard.value.today_focus_minutes}分钟，完成任务${dashboard.value.today_tasks_completed}个`
    const { data } = await request.post('/api/ai/daily-motivation', { stats_context: ctx })
    motivation.value = data.data.message
  } catch (e) {
    motivation.value = '每一天的进步，都是未来的伏笔。'
  } finally {
    loadingMotivation.value = false
  }
}

const reviewChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: dashboard.value.review_trend.map(i => i.date) },
  yAxis: { type: 'value' },
  series: [{ data: dashboard.value.review_trend.map(i => i.count), type: 'line', smooth: true, name: '复习数' }],
}))

const focusChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: dashboard.value.focus_trend.map(i => i.date) },
  yAxis: { type: 'value' },
  series: [{ data: dashboard.value.focus_trend.map(i => i.minutes), type: 'bar', name: '专注分钟' }],
}))
</script>

<template>
  <div>
    <h2>Dashboard</h2>

    <el-alert v-if="motivation" :title="motivation" type="success" :closable="false" show-icon style="margin: 12px 0;" />

    <el-row :gutter="16" style="margin-top: 8px;">
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ dashboard.vocab_count }}</div>
          <div style="color: #6b7280; font-size: 13px;">词条总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ dashboard.due_today }}</div>
          <div style="color: #6b7280; font-size: 13px;">今日到期</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ dashboard.today_reviewed }}</div>
          <div style="color: #6b7280; font-size: 13px;">今日复习</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ dashboard.today_focus_minutes }}</div>
          <div style="color: #6b7280; font-size: 13px;">专注分钟</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ dashboard.today_tasks_completed }}</div>
          <div style="color: #6b7280; font-size: 13px;">完成任务</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover">
          <div style="font-size: 22px; font-weight: 600;">{{ dashboard.due_today }}</div>
          <div style="color: #6b7280; font-size: 13px;">待复习</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px;">
      <template #header>
        <span>快捷入口</span>
      </template>
      <el-space>
        <el-button type="primary" @click="router.push('/review')">开始复习</el-button>
        <el-button @click="router.push('/practice')">去练习</el-button>
        <el-button @click="router.push('/focus')">专注计时</el-button>
        <el-button @click="router.push('/tasks')">任务管理</el-button>
      </el-space>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>近7天复习趋势</template>
          <v-chart :option="reviewChartOption" style="height: 240px;" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>近7天专注趋势</template>
          <v-chart :option="focusChartOption" style="height: 240px;" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
