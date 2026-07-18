<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import UserInfo from '@/components/profile/UserInfo.vue'
import PetList from '@/components/profile/PetList.vue'
import SettingsMenu from '@/components/profile/SettingsMenu.vue'

const router = useRouter()
const { t } = useI18n()
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
      <!-- Header -->
      <div class="flex justify-between items-center py-md mb-md animate-float-up">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full overflow-hidden ring-2 ring-primary-fixed shadow-sm">
            <img class="w-full h-full object-cover" :src="currentUser?.avatar" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-primary font-['Plus_Jakarta_Sans']">PetLumina</span>
        </div>
        <button @click="goToNotifications" class="icon-btn p-2 rounded-full">
          <span class="material-symbols-outlined text-primary">notifications</span>
        </button>
      </div>

      <div class="animate-float-up stagger-1">
        <UserInfo v-if="currentUser" :user="currentUser" @update-avatar="(avatar: string) => userStore.updateAvatar(avatar)" />
      </div>
      <div class="animate-float-up stagger-2">
        <PetList :pets="pets" />
      </div>
      <div class="animate-float-up stagger-3">
        <SettingsMenu />
      </div>

      <!-- Logout Button -->
      <div class="mt-12 px-2 animate-float-up stagger-4">
        <button
          @click="handleLogout"
          class="w-full py-4 rounded-2xl bg-error-container text-on-error-container font-label-bold text-body-md flex items-center justify-center gap-2 btn-jelly depth-1"
        >
          <span class="material-symbols-outlined">logout</span>
          {{ t('profile.logout') }}
        </button>
      </div>
    </main>
  </div>
</template>
