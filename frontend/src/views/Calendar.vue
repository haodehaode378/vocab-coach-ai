<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request.js'

const calendarData = ref({ records: {} })
const streak = ref(0)
const currentDate = ref(new Date())

onMounted(async () => {
  await loadCalendar()
  const { data } = await request.get('/api/checkin/streak')
  streak.value = data.data.current_streak
})

async function loadCalendar() {
  const y = currentDate.value.getFullYear()
  const m = currentDate.value.getMonth() + 1
  const { data } = await request.get(`/api/checkin/calendar?year=${y}&month=${m}`)
  calendarData.value = data.data
}
</script>

<template>
  <div>
    <h2>日历打卡</h2>
    <el-alert :title="`当前连续打卡 ${streak} 天`" type="success" :closable="false" show-icon style="margin: 12px 0; max-width: 480px;" />

    <el-calendar v-model="currentDate" @input="loadCalendar" style="max-width: 800px;">
      <template #date-cell="{ data }">
        <div style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
          <span>{{ data.day.split('-')[2] }}</span>
          <div v-if="calendarData.records[data.day]" style="text-align: center;">
            <el-icon color="#0f766e"><CircleCheckFilled /></el-icon>
          </div>
        </div>
      </template>
    </el-calendar>
  </div>
</template>
