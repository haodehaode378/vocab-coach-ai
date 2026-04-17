<template>
  <div class="relative rounded-lg border-4 border-[#1a1a1a] bg-white p-6 md:p-10 shadow-[6px_6px_0px_0px_rgba(26,26,26,1)]">
    <div v-if="actionLines" class="pointer-events-none absolute -right-3 -top-3 z-10">
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <path d="M10 0 L40 30" stroke="#1a1a1a" stroke-width="4"/>
        <path d="M20 0 L40 20" stroke="#1a1a1a" stroke-width="4"/>
        <path d="M30 0 L40 10" stroke="#1a1a1a" stroke-width="4"/>
      </svg>
    </div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  actionLines: { type: Boolean, default: false },
})
</script>
