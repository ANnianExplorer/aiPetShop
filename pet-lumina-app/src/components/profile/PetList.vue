<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Pet } from '@/types'

const router = useRouter()

defineProps<{
  pets: Pet[]
}>()

const goToAddPet = () => {
  router.push({ name: 'addPet' })
}

const goToPetDetail = (petId: number | string) => {
  router.push({ name: 'petDetail', params: { id: String(petId) } })
}
</script>

<template>
  <section class="mt-12">
    <div class="flex justify-between items-center mb-4">
      <h2 class="font-headline-md text-headline-md text-on-surface">我的宠物</h2>
      <button @click="goToAddPet" class="text-primary text-label-bold font-label-bold flex items-center gap-1 hover:opacity-80">
        添加 <span class="material-symbols-outlined text-sm">add_circle</span>
      </button>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-card-gutter">
      <div 
        v-for="pet in pets" 
        :key="pet.id"
        @click="goToPetDetail(pet.id)"
        class="bg-white rounded-xl p-3 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-white/50 hover:scale-[1.02] transition-transform cursor-pointer"
      >
        <div class="aspect-square rounded-lg overflow-hidden bg-surface-container mb-3">
          <img class="w-full h-full object-cover" :src="pet.avatar" />
        </div>
        <div class="text-center">
          <h3 class="font-title-sm text-[14px] text-on-surface">{{ pet.name }}</h3>
          <p class="text-[11px] text-outline">{{ pet.breed }} · {{ pet.age }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
