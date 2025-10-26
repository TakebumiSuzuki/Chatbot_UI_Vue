<script setup>
  import { ref, computed, nextTick } from 'vue'
  // 末尾に ?component を付けることで、vite-svg-loaderでは、SVGファイルをVueコンポーネントとして直接インポートできる
  // ViteはSVGを静的アセットとして扱うが、vite-svg-loader を導入することで、SVGをVueコンポーネントとして扱えるようになる。
  import SendIcon from '../assets/icons/Send.svg?component'

  const props = defineProps({
    disabled: {
      type: Boolean,
      default: false
    }
  })

  const emit = defineEmits(['sendMessage'])

  const userInput = ref('')
  const maxChars = 200

  const charCount = computed(() => userInput.value.length)

  const handleSubmit = () => {
    if (userInput.value.trim() && !props.disabled) {
      emit('sendMessage', userInput.value.trim())
      userInput.value = '' // Clear input after sending
    }
  }

  const textarea = ref(null)

  const autoResize = async () => {
    await nextTick()
    const el = textarea.value
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
    console.log(el.style.height)
  }

</script>


<template>
  <form
    @submit.prevent="handleSubmit"
    class="flex items-center gap-2.5 pl-4 pr-1.5 py-1.5 bg-gray-700 rounded-2xl transition-all focus-within:ring-2 focus-within:ring-blue-500 mb-2"
    :class="{ 'opacity-60': disabled }"
  >
    <!-- maxlength はHTMLの <textarea> 要素が持つ標準の属性 -->
    <textarea
      v-model="userInput"
      ref="textarea"
      @input="autoResize"
      :disabled="disabled"
      :maxlength="maxChars"
      placeholder="Type your message..."
      class="grow w-full resize-none focus:outline-none"
      rows="1"

    ></textarea>

    <div class="shrink-0 text-xs text-gray-300 self-end">
      {{ charCount}} / {{ maxChars }}
    </div>

    <button
      type="submit"
      :disabled="disabled || charCount === 0"
      class="shrink-0 pl-2.5 py-2 pr-1.5 rounded-full bg-linear-to-br from-blue-600 to-purple-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:cursor-pointer hover:scale-107"
      aria-label="Send message"
    >
      <SendIcon class="w-4 h-4 text-gray-50" />
    </button>
  </form>
  <!-- 標準のHTMLの <textarea> 要素は、右下にツマミ（ハンドル）が表示され、ユーザーがドラッグして自由にサイズを変更できます。
    esize-none は、CSSの resize: none; に相当し、このリサイズ機能を無効にします。-->
</template>