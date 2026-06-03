<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<template>
  <div class="min-h-screen relative">
    <!-- Ambient decorative glows -->
    <div class="fixed top-[-10%] left-[-5%] w-[40%] h-[40%] bg-primary-fixed-dim/30 blur-[120px] rounded-full pointer-events-none animate-ambient z-[-1]" />
    <div class="fixed bottom-[5%] right-[-5%] w-[35%] h-[35%] bg-secondary-container/20 blur-[100px] rounded-full pointer-events-none animate-ambient z-[-1]" style="animation-delay: -4s" />

    <Sidebar />
    <Header />
    <main class="ml-64 p-8">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>
