<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import type { User, Post } from '@/types'
import { userApi } from '@/api/user'
import { postApi } from '@/api/post'
import { followApi } from '@/api/follow'

const route = useRoute()
const router = useRouter()
const { showToast } = useToast()

const userId = computed(() => Number(route.params.id))

const user = ref<User | null>(null)
const userPosts = ref<Post[]>([])
const isFollowing = ref(false)
const followersCount = ref(0)
const followingCount = ref(0)

const fetchUser = async () => {
  try {
    const res = await userApi.getById(userId.value) as any
    user.value = res
  } catch (e) {
    console.error('Failed to fetch user:', e)
  }
}

const fetchPosts = async () => {
  try {
    const res = await postApi.listPage({ authorId: userId.value, pageSize: 20 }) as any
    userPosts.value = res?.records || []
  } catch (e) {
    console.error('Failed to fetch posts:', e)
  }
}

const fetchFollowData = async () => {
  try {
    const [followersRes, followingRes] = await Promise.all([
      followApi.listFollowers({ pageSize: 1 }),
      followApi.listFollowing({ pageSize: 1 }),
    ])
    followersCount.value = (followersRes as any)?.total ?? 0
    followingCount.value = (followingRes as any)?.total ?? 0
  } catch (e) {
    console.error('Failed to fetch follow data:', e)
  }
}

onMounted(async () => {
  await fetchUser()
  if (user.value) {
    await Promise.all([fetchPosts(), fetchFollowData()])
  }
})

const goBack = () => {
  router.back()
}

const toggleFollow = async () => {
  try {
    await followApi.toggle(userId.value)
    isFollowing.value = !isFollowing.value
    followersCount.value += isFollowing.value ? 1 : -1
    showToast(isFollowing.value ? '已关注' : '已取消关注', 'success')
  } catch (e) {
    console.error('Failed to toggle follow:', e)
  }
}

const goToPostDetail = (postId: number) => {
  router.push({ name: 'postDetail', params: { id: postId } })
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main v-if="user" class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">用户主页</span>
        <div class="w-10"></div>
      </div>

      <section class="bg-surface-container-low rounded-xl p-6 text-center">
        <img :src="user.avatar" class="w-20 h-20 rounded-full object-cover mx-auto mb-4 border-4 border-primary" />
        <h1 class="font-headline-sm text-headline-sm text-on-surface">{{ user.nickname }}</h1>
        <p class="text-body-sm text-on-surface-variant mt-1">{{ user.location }}</p>
        <p class="text-body-md text-on-surface mt-3">{{ user.bio }}</p>

        <div class="flex justify-center gap-8 mt-6 pt-6 border-t border-outline-variant/20">
          <div class="text-center">
            <p class="font-title-md text-title-md text-on-surface">{{ userPosts.length }}</p>
            <p class="text-label-sm text-on-surface-variant">帖子</p>
          </div>
          <div class="text-center">
            <p class="font-title-md text-title-md text-on-surface">{{ followersCount }}</p>
            <p class="text-label-sm text-on-surface-variant">粉丝</p>
          </div>
          <div class="text-center">
            <p class="font-title-md text-title-md text-on-surface">{{ followingCount }}</p>
            <p class="text-label-sm text-on-surface-variant">关注</p>
          </div>
        </div>

        <button 
          @click="toggleFollow"
          class="mt-6 w-full py-3 rounded-full font-title-sm text-title-sm transition-all active:scale-95"
          :class="isFollowing ? 'bg-surface-container-high text-on-surface' : 'bg-primary text-on-primary'"
        >
          {{ isFollowing ? '已关注' : '关注' }}
        </button>
      </section>

      <section>
        <h2 class="font-title-sm text-title-sm text-on-surface mb-4">TA 的帖子</h2>
        <div class="space-y-4">
          <div
            v-for="post in userPosts"
            :key="post.id"
            @click="goToPostDetail(post.id)"
            class="bg-surface-container-low rounded-xl overflow-hidden shadow-sm cursor-pointer active:scale-95 transition-transform"
          >
            <img v-if="post.imageList?.length > 0" :src="post.imageList[0]" class="w-full h-40 object-cover" />
            <div class="p-4">
              <p class="text-body-md text-on-surface leading-relaxed">{{ post.content }}</p>
              <div class="flex items-center gap-4 mt-3">
                <div class="flex items-center gap-1 text-outline-variant">
                  <span class="material-symbols-outlined text-sm">favorite</span>
                  <span class="text-xs">{{ post.likes }}</span>
                </div>
                <div class="flex items-center gap-1 text-outline-variant">
                  <span class="material-symbols-outlined text-sm">chat_bubble</span>
                  <span class="text-xs">{{ post.comments }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <div v-else class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">error_outline</span>
      <p class="mt-4 font-title-md text-on-surface-variant">用户不存在</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">返回</button>
    </div>
  </div>
</template>
