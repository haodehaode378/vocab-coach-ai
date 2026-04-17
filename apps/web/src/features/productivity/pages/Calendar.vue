<script setup>
import { ref, onMounted } from 'vue'
import request from '../../../api/request.js'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

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
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">日历打卡</h2>
      <ComicBadge variant="success">YEAH!</ComicBadge>
    </div>

    <ComicCard class="inline-flex items-center gap-3">
      <div class="text-3xl">🔥</div>
      <div class="font-black text-xl">当前连续打卡 {{ streak }} 天</div>
    </ComicCard>

    <el-calendar v-model="currentDate" @input="loadCalendar" class="w-full max-w-4xl">
      <template #date-cell="{ data }">
        <div class="flex h-full flex-col justify-between">
          <span class="font-bold">{{ data.day.split('-')[2] }}</span>
          <div v-if="calendarData.records[data.day]" class="text-center">
            <el-icon class="text-lg text-[#06ffa5]"><CircleCheckFilled /></el-icon>
          </div>
        </div>
      </template>
    </el-calendar>
  </div>
</template>

