<template>
  <div class="rounded-lg border-4 border-[#1a1a1a] bg-[#fffef0] p-4 md:p-6 shadow-[4px_4px_0px_0px_rgba(26,26,26,1)] transition-all duration-150"
       :class="{ 'hover:shadow-[2px_2px_0px_0px_rgba(26,26,26,1)] hover:translate-x-[2px] hover:translate-y-[2px]': hoverable }">
    <div v-if="$slots.header" class="mb-4 border-b-4 border-[#1a1a1a] pb-3">
      <slot name="header" />
    </div>
    <slot />
    <div v-if="$slots.footer" class="mt-4 border-t-4 border-[#1a1a1a] pt-3">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  hoverable: { type: Boolean, default: false },
})
</script>
