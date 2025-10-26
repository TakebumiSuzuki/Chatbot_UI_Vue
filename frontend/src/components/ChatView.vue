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
    // 必要であれば、過去のチャット履歴をサーバーから取得するリクエストなどを送信

    // --- WebSocket 接続を開始 ---
    // 実際のURLに置き換えてください
    socket = new WebSocket('ws://your-websocket-server.com/chat')

    // 接続が確立したときの処理
    socket.onopen = () => {
      console.log('WebSocket connection established.')
    }

    // メッセージを受信したときの処理
    socket.onmessage = (event) => {
      const messageData = JSON.parse(event.data) // サーバーからのデータ形式に合わせる

      // AIの返信をストリーミングで受け取る場合の処理例
      const aiMessage = chatHistory.value.find(m => m.id === messageData.id)
      if (aiMessage) {
        // 既存のメッセージを更新
        aiMessage.content += messageData.chunk // 'chunk'はサーバーから送られる部分的なテキスト
        if (messageData.isFinal) { // メッセージの最後を示すフラグ
          isLoading.value = false
        }
      } else {
        // 新しいメッセージとして追加
        chatHistory.value.push({
          id: messageData.id,
          role: 'ai',
          content: messageData.chunk
        })
        isLoading.value = true // ストリーミング開始
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


  // onMounted(async () => {
  //   try {
  //     const response = await fetch('/dummy-chat-history.json')
  //     if (!response.ok) throw new Error('Network response was not ok')
  //     chatHistory.value = await response.json()
  //     scrollToBottom()
  //   } catch (error) {
  //     console.error('Failed to fetch chat history:', error)
  //     chatHistory.value.push({
  //       id: Date.now(),
  //       role: 'error',
  //       content: 'Failed to load chat history.'
  //     })
  //   }
  // })

  const handleSendMessage = (userInput) => {
    if (isLoading.value || !socket || socket.readyState !== WebSocket.OPEN) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: userInput
    }
    chatHistory.value.push(userMessage)
    scrollToBottom()

    // WebSocketサーバーにメッセージを送信
    socket.send(JSON.stringify({ content: userInput }))

    isLoading.value = true
    
    const aiResponseId = Date.now() + 1
    chatHistory.value.push({
      id: aiResponseId,
      role: 'ai',
      content: ''
    })
    scrollToBottom()

    // 3. Simulate AI response with typewriter effect
    const dummyResponse = "This is a simulated response with a typewriter effect. I am processing your request and this text is generated to demonstrate the animation."
    const aiMessage = chatHistory.value.find(m => m.id === aiResponseId)

    let i = 0
    const interval = setInterval(() => {
      if (i < dummyResponse.length) {
        aiMessage.content += dummyResponse.charAt(i)
        i++
        scrollToBottom()
      } else {
        clearInterval(interval)
        isLoading.value = false // 4. Stop loading
      }
    }, 30) // Typewriter speed (milliseconds)
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
        <!-- <div v-if="isLoading" class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full shrink-0 bg-green-700"></div>
            <LoaderIcon class="w-6 h-6 animate-spin text-gray-400" />
        </div> -->
      </div>
    </div>

    <div class="px-4 pt-1.5 pb-3 bg-gray-900/80 backdrop-blur-sm">
      <ChatInput @sendMessage="handleSendMessage" :disabled="isLoading" />
    </div>

  </div>
</template>