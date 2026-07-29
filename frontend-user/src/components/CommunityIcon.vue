<script setup lang="ts">
defineProps<{
  name: 'heart' | 'comment' | 'bookmark' | 'send' | 'sparkles' | 'map'
}>()
</script>

<template>
  <svg
    class="community-icon"
    viewBox="0 0 24 24"
    width="20"
    height="20"
    aria-hidden="true"
  >
    <path
      v-if="name === 'heart'"
      d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78Z"
    />
    <path
      v-else-if="name === 'comment'"
      d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z"
    />
    <path
      v-else-if="name === 'bookmark'"
      d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1Z"
    />
    <path v-else-if="name === 'send'" d="m22 2-7 20-4-9-9-4 20-7Z" />
    <path
      v-else-if="name === 'sparkles'"
      d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3Zm7 11 .8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14ZM5 13l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3Z"
    />
    <path
      v-else
      d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Zm-8-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"
    />
  </svg>
</template>

<style scoped>
.community-icon {
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
