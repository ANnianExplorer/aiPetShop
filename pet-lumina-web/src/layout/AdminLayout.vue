<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<template>
  <div class="min-h-screen">
    <Sidebar />
    <Header />
    <main class="ml-72 p-8">
      <router-view />
    </main>
  </div>
</template>
