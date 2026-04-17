<script setup>
import { ref, onMounted } from 'vue'
import request from '../../../api/request.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import ComicCard from '../../../components/comic/ComicCard.vue'
import ComicButton from '../../../components/comic/ComicButton.vue'
import ComicBadge from '../../../components/comic/ComicBadge.vue'

const tasks = ref([])
const filterStatus = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({ id: null, title: '', description: '', priority: 'medium', due_date: '', status: 'todo' })

onMounted(loadTasks)

async function loadTasks() {
  const { data } = await request.get(`/api/tasks?status=${filterStatus.value}`)
  tasks.value = data.data
}

function openCreate() {
  isEdit.value = false
  form.value = { id: null, title: '', description: '', priority: 'medium', due_date: '', status: 'todo' }
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  form.value = { ...row, due_date: row.due_date ? row.due_date.slice(0, 16) : '' }
  dialogVisible.value = true
}

async function save() {
  const payload = { ...form.value }
  if (payload.due_date) payload.due_date = new Date(payload.due_date).toISOString()
  if (isEdit.value) {
    await request.put(`/api/tasks/${payload.id}`, payload)
  } else {
    await request.post('/api/tasks', payload)
  }
  dialogVisible.value = false
  await loadTasks()
}

async function remove(id) {
  await ElMessageBox.confirm('确定删除该任务？', '提示', { type: 'warning' })
  await request.delete(`/api/tasks/${id}`)
  await loadTasks()
}

const priorityVariant = (p) => ({ high: 'danger', medium: 'warning', low: 'secondary' }[p] || 'secondary')
const statusVariant = (s) => ({ todo: 'secondary', done: 'success' }[s] || 'secondary')
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h2 class="font-black text-2xl uppercase tracking-wide text-[#1a1a1a] md:text-4xl">任务管理</h2>
        <ComicBadge variant="warning">TASK!</ComicBadge>
      </div>
      <ComicButton variant="primary" @click="openCreate">新建任务</ComicButton>
    </div>

    <div class="flex flex-wrap gap-2">
      <ComicButton :variant="filterStatus === '' ? 'dark' : 'light'" size="sm" @click="filterStatus = ''; loadTasks()">全部</ComicButton>
      <ComicButton :variant="filterStatus === 'todo' ? 'dark' : 'light'" size="sm" @click="filterStatus = 'todo'; loadTasks()">进行中</ComicButton>
      <ComicButton :variant="filterStatus === 'done' ? 'dark' : 'light'" size="sm" @click="filterStatus = 'done'; loadTasks()">已完成</ComicButton>
    </div>

    <div class="space-y-3">
      <ComicCard v-for="row in tasks" :key="row.id" hoverable>
        <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <div class="font-black text-lg text-[#1a1a1a]">{{ row.title }}</div>
            <div class="text-sm font-bold text-[#1a1a1a]/70">{{ row.description || '暂无描述' }}</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <ComicBadge :variant="priorityVariant(row.priority)">{{ row.priority }}</ComicBadge>
            <ComicBadge :variant="statusVariant(row.status)">{{ row.status }}</ComicBadge>
            <ComicButton variant="light" size="sm" @click="openEdit(row)">编辑</ComicButton>
            <ComicButton variant="danger" size="sm" @click="remove(row.id)">删除</ComicButton>
          </div>
        </div>
      </ComicCard>
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑任务' : '新建任务'" width="480px">
      <div class="space-y-4">
        <div>
          <div class="mb-1 font-bold">标题</div>
          <el-input v-model="form.title" />
        </div>
        <div>
          <div class="mb-1 font-bold">描述</div>
          <el-input v-model="form.description" type="textarea" />
        </div>
        <div>
          <div class="mb-1 font-bold">优先级</div>
          <el-select v-model="form.priority" class="w-full">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </div>
        <div>
          <div class="mb-1 font-bold">截止日期</div>
          <el-date-picker v-model="form.due_date" type="datetime" class="w-full" />
        </div>
        <div v-if="isEdit">
          <div class="mb-1 font-bold">状态</div>
          <el-select v-model="form.status" class="w-full">
            <el-option label="进行中" value="todo" />
            <el-option label="已完成" value="done" />
          </el-select>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <ComicButton variant="light" @click="dialogVisible = false">取消</ComicButton>
          <ComicButton variant="primary" @click="save">保存</ComicButton>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

