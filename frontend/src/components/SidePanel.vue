<script setup>
  import { ref } from 'vue'

  // Spec: This variable will hold the source content in the future.
  const sourceContext = ref('');
</script>

<template>
  <div class="p-4 h-full">
    <h2 class="text-lg font-bold mb-4">Information Source</h2>
    <div class="p-4 h-[calc(100%-40px)] overflow-y-auto">
      <p v-if="!sourceContext" class="text-gray-400">
        Source content will appear here.
      </p>
      <div v-else>
        {{ sourceContext }}
      </div>
    </div>
  </div>
</template>