<script setup>
  import { ref, onMounted, nextTick, onUnmounted } from 'vue'
  import ChatMessage from './ChatMessage.vue'
  import ChatInput from './ChatInput.vue'
  import LoaderIcon from '../assets/icons/Loader2.svg?component'

  const chatHistory = ref([])
  const isLoading = ref(false)
  const chatContainer = ref(null)

  let socket = null


  // Helper function to scroll to the bottom of the chat
  const scrollToBottom = () => {
    nextTick(() => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    })
  }

  onMounted(() => {
    // ここに必要であれば、過去のチャット履歴をサーバーから取得するリクエストなどを送信
    // chatHistory = ...

    // 実際のURLに置き換えてください
    // このコードを実行した時点で、ブラウザは指定されたURLのサーバーに対してWebSocket接続の確立を非同期に開始する
    socket = new WebSocket('ws://your-websocket-server.com/chat')

    // 接続が確立したときの処理
    socket.onopen = () => {
      console.log('WebSocket connection established.')
    }

    // メッセージを受信したときの処理
    socket.onmessage = (event) => {
      isLoading.value = false
      const messageData = JSON.parse(event.data) // サーバーからのデータ形式に合わせる

      // AIの返信をストリーミングで受け取る場合の処理例
      const aiMessage = chatHistory.value.find(m => m.id === messageData.id)
      if (aiMessage) {
        // 既存のメッセージを更新
        aiMessage.content += messageData.chunk // 'chunk'はサーバーから送られる部分的なテキスト
        if (messageData.isFinal) { // メッセージの最後を示すフラグ

        }
      } else {
        // 新しいメッセージとして追加
        chatHistory.value.push({
          id: messageData.id,
          role: 'ai',
          content: messageData.chunk
        })

      }
      scrollToBottom()
    }

    // エラーが発生したときの処理
    socket.onerror = (error) => {
      console.error('WebSocket Error:', error)
      chatHistory.value.push({
        id: Date.now(),
        role: 'error',
        content: 'Connection error occurred.'
      })
      isLoading.value = false
    }

    // 接続が閉じたときの処理
    socket.onclose = () => {
      console.log('WebSocket connection closed.')
      isLoading.value = false
    }
  })

  // コンポーネントが破棄されるときに接続を閉じる
  onUnmounted(() => {
    if (socket) {
      socket.close()
    }
  })

  const handleSendMessage = (userInput) => {
    if (isLoading.value || !socket || socket.readyState !== WebSocket.OPEN) return

    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: userInput
    }
    chatHistory.value.push(userMessage)
    scrollToBottom()

    // WebSocketサーバーにメッセージを送信
    socket.send(JSON.stringify({ content: userInput }))

    isLoading.value = true
  }
</script>


<template>
  <div class="flex flex-col h-full">
    <!-- overflow-y-auto は、要素の高さを内容が超えた場合にのみ、縦方向のスクロールバーを表示する。デフォルト値は visible -->
    <div ref="chatContainer" class="grow px-4 pt-12 pb-3 overflow-y-auto">
      <div class="space-y-6">
        <ChatMessage
          v-for="message in chatHistory"
          :key="message.id"
          :message="message"
        />
        <div v-if="isLoading" class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full shrink-0 bg-green-700"></div>
            <LoaderIcon class="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </div>
    </div>

    <div class="px-4 pt-1.5 pb-3 bg-gray-900/80 backdrop-blur-sm">
      <ChatInput @sendMessage="handleSendMessage" :disabled="isLoading" />
    </div>

  </div>
</template>