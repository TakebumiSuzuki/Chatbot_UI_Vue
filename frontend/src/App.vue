<script setup>
  import { onMounted } from 'vue'
  import Split from 'split.js'
  import SidePanel from './components/SidePanel.vue'
  import ChatView from './components/ChatView.vue'

  onMounted(() => {
    // Split.js を使う場合、親要素に必ず display: flex が必要。splitは、登録した要素に flex-basis を適用するので。
    Split(['#side-panel', '#chat-view'], {
      sizes: [50, 50],
      minSize: [300, 300],
      gutterSize: 3,
      // 以下の関数は、初期化時と gutter のドラッグ中に呼ばれる(これにより、リアルタイムにサイズ変更している)
      // デフォルトでも設定されているので、以下は消去しても問題なく動く
      elementStyle: (dimension, size, gutterSize) => ({
        'flex-basis': `calc(${size}% - ${gutterSize}px / 2)`,
      }),
      gutterStyle: (dimension, gutterSize) => ({
        'flex-basis': `${gutterSize}px`,
      }),
    })
  })
</script>

<template>
  <main class="flex flex-row h-screen">
    <div id="side-panel" class="h-full bg-gray-800">
      <SidePanel />
    </div>
    <div id="chat-view" class="h-full bg-gray-900">
      <ChatView />
    </div>
  </main>
</template>


<style>
  /* Styles for the gutter element created by split.js */
  .gutter {
    background-color: #374151; /* bg-gray-800 */
  }

  .gutter.gutter-horizontal {
    cursor: col-resize;
  }
</style>
