import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../../features/analytics/pages/Dashboard.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/study', name: 'Study', component: () => import('../../features/learning/pages/Study.vue') },
  { path: '/review', name: 'Review', component: () => import('../../features/learning/pages/Study.vue') },
  { path: '/practice', name: 'Practice', component: () => import('../../features/learning/pages/Practice.vue') },
  { path: '/vocab', name: 'Vocab', component: () => import('../../features/learning/pages/Vocab.vue') },
  { path: '/focus', name: 'Focus', component: () => import('../../features/productivity/pages/Focus.vue') },
  { path: '/tasks', name: 'Tasks', component: () => import('../../features/productivity/pages/Tasks.vue') },
  { path: '/calendar', name: 'Calendar', component: () => import('../../features/productivity/pages/Calendar.vue') },
  { path: '/chat', name: 'Chat', component: () => import('../../features/intelligence/pages/Chat.vue') },
  { path: '/progress', name: 'Progress', component: () => import('../../features/analytics/pages/Progress.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
