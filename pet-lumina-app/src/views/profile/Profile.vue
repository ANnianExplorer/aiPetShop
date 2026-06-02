<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import UserInfo from '@/components/profile/UserInfo.vue'
import PetList from '@/components/profile/PetList.vue'
import SettingsMenu from '@/components/profile/SettingsMenu.vue'

const router = useRouter()
const userStore = useUserStore()
const { currentUser, pets } = storeToRefs(userStore)

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex justify-between items-center py-md mb-md">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full overflow-hidden ring-2 ring-primary-fixed">
            <img class="w-full h-full object-cover" :src="currentUser?.avatar" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-emerald-800">PetLumina</span>
        </div>
        <button @click="goToNotifications" class="text-zinc-400 hover:bg-emerald-50 transition-colors p-2 rounded-full active:scale-95 duration-200">
          <span class="material-symbols-outlined">notifications</span>
        </button>
      </div>
      <UserInfo v-if="currentUser" :user="currentUser" @update-avatar="(avatar: string) => userStore.updateAvatar(avatar)" />
      <PetList :pets="pets" />
      <SettingsMenu />

      <!-- Logout Button -->
      <div class="mt-12 px-2">
        <button 
          @click="handleLogout"
          class="w-full py-4 rounded-xl bg-error-container text-on-error-container font-label-bold text-body-md flex items-center justify-center gap-2 active:scale-95 transition-transform"
        >
          <span class="material-symbols-outlined">logout</span>
          退出登录
        </button>
      </div>
    </main>
  </div>
</template>
