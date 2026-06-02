<script setup lang="ts">
import { ref, watch } from 'vue'
import { userApi } from '@/api/user'

const props = defineProps<{ visible: boolean; userId: number }>()
const emit = defineEmits(['update:visible'])

const userData = ref<any>(null)
const loading = ref(false)

watch(() => props.visible, async (val) => {
  if (val && props.userId) {
    loading.value = true
    try {
      userData.value = await userApi.getDetail(props.userId)
    } catch (e) {
      console.error('Failed to fetch user detail:', e)
    } finally {
      loading.value = false
    }
  }
})

const handleClose = () => {
  emit('update:visible', false)
}
</script>

<template>
  <el-drawer :model-value="visible" title="用户详情" size="500px" @close="handleClose">
    <div v-loading="loading" v-if="userData" class="space-y-5 p-1">
      <!-- User Info -->
      <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center gap-4">
          <el-avatar :size="64" :src="userData.user?.avatar" class="user-avatar">
            {{ userData.user?.nickname?.charAt(0) || 'U' }}
          </el-avatar>
          <div>
            <h3 class="font-[Plus_Jakarta_Sans] text-lg font-bold text-on-surface m-0">{{ userData.user?.nickname }}</h3>
            <p class="text-sm text-on-surface-variant mt-1">{{ userData.user?.email }}</p>
            <p class="text-sm text-on-surface-variant">{{ userData.user?.phone }}</p>
          </div>
        </div>
      </div>

      <!-- Pets -->
      <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">pets</span>
          <h4 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-sm">宠物列表 ({{ userData.pets?.length || 0 }})</h4>
        </div>
        <div class="flex flex-col gap-3">
          <div v-for="pet in userData.pets" :key="pet.id" class="flex items-center gap-3 p-3 rounded-xl bg-white/10 backdrop-blur-sm">
            <el-avatar :size="36" :src="pet.avatar" class="pet-avatar">{{ pet.name?.charAt(0) }}</el-avatar>
            <div class="flex flex-col">
              <span class="font-semibold text-sm text-on-surface">{{ pet.name }}</span>
              <span class="text-xs text-on-surface-variant">{{ pet.breed }} &middot; {{ pet.type }}</span>
            </div>
          </div>
          <el-empty v-if="!userData.pets?.length" description="暂无宠物" :image-size="60" />
        </div>
      </div>

      <!-- Recent Posts -->
      <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">article</span>
          <h4 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-sm">最近帖子 ({{ userData.posts?.length || 0 }})</h4>
        </div>
        <div class="flex flex-col gap-3">
          <div v-for="post in userData.posts" :key="post.id" class="p-3 rounded-xl bg-white/10 backdrop-blur-sm">
            <p class="text-sm text-on-surface-variant mb-2">{{ post.content?.substring(0, 80) }}{{ post.content?.length > 80 ? '...' : '' }}</p>
            <div class="flex justify-between text-xs text-on-surface-variant/70">
              <span>{{ post.createTime }}</span>
              <span class="flex items-center gap-2">
                <span class="flex items-center gap-1"><span class="material-symbols-outlined text-xs">favorite</span>{{ post.likes }}</span>
                <span class="flex items-center gap-1"><span class="material-symbols-outlined text-xs">chat_bubble</span>{{ post.comments }}</span>
              </span>
            </div>
          </div>
          <el-empty v-if="!userData.posts?.length" description="暂无帖子" :image-size="60" />
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.user-avatar {
  background: var(--color-primary-container);
  color: white;
  font-size: 24px;
  font-weight: 700;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.pet-avatar {
  background: rgba(109, 175, 146, 0.2);
  color: var(--color-primary-container);
  font-weight: 600;
}
</style>
