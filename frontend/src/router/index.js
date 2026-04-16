import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/study', name: 'Study', component: () => import('../views/Study.vue') },
  { path: '/review', name: 'Review', component: () => import('../views/Study.vue') },
  { path: '/practice', name: 'Practice', component: () => import('../views/Practice.vue') },
  { path: '/vocab', name: 'Vocab', component: () => import('../views/Vocab.vue') },
  { path: '/focus', name: 'Focus', component: () => import('../views/Focus.vue') },
  { path: '/tasks', name: 'Tasks', component: () => import('../views/Tasks.vue') },
  { path: '/calendar', name: 'Calendar', component: () => import('../views/Calendar.vue') },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue') },
  { path: '/progress', name: 'Progress', component: () => import('../views/Progress.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
