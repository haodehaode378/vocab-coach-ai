<template>
  <span class="inline-flex items-center rounded-lg border-4 border-[#1a1a1a] px-2 py-0.5 text-xs font-black uppercase tracking-wide shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]"
        :class="colorClasses">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'primary' },
})

const colorClasses = computed(() => ({
  primary: 'bg-[#ff006e] text-white',
  secondary: 'bg-[#3a86ff] text-white',
  success: 'bg-[#06ffa5] text-[#1a1a1a]',
  warning: 'bg-[#ffbe0b] text-[#1a1a1a]',
  danger: 'bg-[#fb5607] text-white',
  dark: 'bg-[#1a1a1a] text-white',
  light: 'bg-[#fffef0] text-[#1a1a1a]',
}[props.variant]))
</script>
