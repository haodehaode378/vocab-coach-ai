<template>
  <input
    :value="modelValue"
    :type="type"
    :placeholder="placeholder"
    :disabled="disabled"
    class="w-full rounded-lg border-4 border-[#1a1a1a] bg-white px-3 py-2 md:px-4 md:py-3 text-sm md:text-base font-bold text-[#1a1a1a] placeholder:text-[#1a1a1a]/60 focus:shadow-[4px_4px_0px_0px_rgba(26,26,26,1)] focus:outline-none transition-all duration-150"
    @input="$emit('update:modelValue', $event.target.value)"
    @keyup.enter="$emit('enter', $event)"
  />
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
defineEmits(['update:modelValue', 'enter'])
</script>
