<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request.js'
import { ElMessage, ElMessageBox } from 'element-plus'

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

const priorityTag = (p) => ({ high: 'danger', medium: 'warning', low: 'info' }[p] || 'info')
const statusTag = (s) => ({ todo: 'info', done: 'success' }[s] || 'info')
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2>任务管理</h2>
      <el-button type="primary" @click="openCreate">新建任务</el-button>
    </div>

    <div style="margin: 12px 0;">
      <el-radio-group v-model="filterStatus" @change="loadTasks">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="todo">进行中</el-radio-button>
        <el-radio-button label="done">已完成</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="tasks" style="width: 100%;">
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="priorityTag(row.priority)">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button text @click="openEdit(row)">编辑</el-button>
          <el-button text type="danger" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑任务' : '新建任务'" width="480px">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="form.due_date" type="datetime" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="form.status">
            <el-option label="进行中" value="todo" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
