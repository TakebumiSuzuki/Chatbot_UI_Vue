<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    message: {
      type: Object,
      required: true
    }
  })

  // The role of the message determines its appearance
  const isUser = computed(() => props.message.role === 'user')
  const isAi = computed(() => props.message.role === 'ai')
  const isError = computed(() => props.message.role === 'error')
</script>

<template>
  <div class="flex items-start gap-3" :class="{ 'justify-end': isUser }">
    <!-- AI/Error Icon Placeholder (Left) -->
    <div
      v-if="isAi"
      class="w-9 h-9 rounded-full shrink-0 bg-purple-500"
    ></div>

    <!-- Message Bubble -->
    <div
      class="max-w-2xl py-2.5 px-4 rounded-lg block"
      :class="{
        'bg-linear-to-br from-blue-600 to-purple-600 text-white': isUser,
        'bg-gray-700 text-white': isAi,
        'bg-red-500/20 text-red-300 border border-red-300/50 mx-auto': isError
      }"
    >
      <p class="whitespace-pre-wrap">{{ message.content }}</p>
    </div>

    <!-- User Icon Placeholder (Right) -->
    <div
      v-if="isUser"
      class="w-9 h-9 rounded-full shrink-0 bg-indigo-700"
    ></div>
  </div>
</template>