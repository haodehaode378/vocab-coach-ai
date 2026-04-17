<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center rounded-lg border-4 border-[#1a1a1a] font-black uppercase tracking-wide transition-all duration-150 active:translate-x-[4px] active:translate-y-[4px] disabled:cursor-not-allowed"
    :class="[
      sizeClasses,
      colorClasses,
      shadowClass,
      hoverClass,
      { 'opacity-70': disabled || loading }
    ]"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-lg border-2 border-white border-t-transparent"></span>
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

defineEmits(['click'])

const sizeClasses = computed(() => ({
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-8 py-3.5 text-base',
}[props.size]))

const colorClasses = computed(() => ({
  primary: 'bg-[#ff006e] text-white',
  secondary: 'bg-[#3a86ff] text-white',
  success: 'bg-[#06ffa5] text-[#1a1a1a]',
  warning: 'bg-[#ffbe0b] text-[#1a1a1a]',
  danger: 'bg-[#fb5607] text-white',
  dark: 'bg-[#1a1a1a] text-white',
  light: 'bg-[#fffef0] text-[#1a1a1a]',
}[props.variant]))

const shadowClass = computed(() => {
  const map = {
    primary: 'shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]',
    secondary: 'shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]',
    success: 'shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]',
    warning: 'shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]',
    danger: 'shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]',
    dark: 'shadow-[4px_4px_0px_0px_rgba(255,0,110,1)]',
    light: 'shadow-[4px_4px_0px_0px_rgba(26,26,26,1)]',
  }
  return map[props.variant]
})

const hoverClass = computed(() => {
  const map = {
    primary: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]',
    secondary: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]',
    success: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]',
    warning: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]',
    danger: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]',
    dark: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(255,0,110,1)]',
    light: 'hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]',
  }
  return map[props.variant]
})
</script>
