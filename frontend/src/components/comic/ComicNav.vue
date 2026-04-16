<template>
  <aside class="flex h-full w-16 flex-col border-r-4 border-[#1a1a1a] bg-white md:w-56">
    <div class="flex h-16 items-center justify-center border-b-4 border-[#1a1a1a] px-4 md:justify-start">
      <span class="hidden font-black text-xl tracking-wider text-[#1a1a1a] md:inline">AI 学习助手</span>
      <span class="font-black text-xl text-[#1a1a1a] md:hidden">AI</span>
    </div>
    <nav class="flex-1 overflow-y-auto py-4">
      <ul class="space-y-2 px-2 md:px-4">
        <li v-for="m in menus" :key="m.index">
          <router-link
            :to="m.index"
            class="flex items-center gap-3 rounded-lg border-4 border-transparent px-3 py-2 font-black text-sm uppercase tracking-wide text-[#1a1a1a] transition-all duration-150 hover:border-[#1a1a1a] hover:bg-[#fffef0] hover:shadow-[3px_3px_0px_0px_rgba(26,26,26,1)]"
            :class="{ 'border-[#1a1a1a] bg-[#ffbe0b] shadow-[3px_3px_0px_0px_rgba(26,26,26,1)]': isActive(m.index) }"
          >
            <el-icon class="text-lg">
              <component :is="m.icon" />
            </el-icon>
            <span class="hidden md:inline">{{ m.title }}</span>
          </router-link>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

defineProps({
  menus: { type: Array, required: true },
})

function isActive(index) {
  return route.path === index
}
</script>
