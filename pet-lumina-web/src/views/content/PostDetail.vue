<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const postData = ref({
  id: Number(route.params.id),
  category: 'Pet Health',
  title: '萨摩耶幼犬春季护理指南：从饮食到梳毛的全方位心得',
  publishTime: '2024年3月15日 14:30',
  content: [
    '春天到了，家里的萨摩耶正处于换毛期。作为一名三年的"萨摩爸"，我总结了一些关于春季护理的关键点分享给大家。首先是饮食，春季细菌活跃，一定要注意食具的清洁...',
    '其次是毛发护理。大家都知道萨摩耶的毛发非常厚实，如果每天不进行至少一次的深层梳理，家里很快就会变成"雪场"。我推荐使用那种带弧度的排梳，可以有效勾掉底层的死毛而不伤皮肤。',
    '最后是户外运动。春季草坪上寄生虫开始复苏，遛狗回来一定要仔细检查爪垫和耳根，防虫喷雾必不可少。',
  ],
  images: [
    'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400&h=300&fit=crop',
  ],
  likes: 1284,
  comments: 456,
  views: '12.5k',
  author: {
    name: '萨摩耶阿黄的日常',
    bio: '资深宠物博主 / 动物医学专业 / 萨摩耶爱好者',
    followers: '15.2k',
    totalLikes: '88.4k',
  },
  status: 'pending',
})

const auditNote = ref('系统已初步完成敏感词过滤，未发现违规项。请根据社区准则进行人工复核。')

onMounted(async () => {
  loading.value = true
  try { /* const res = await postApi.getDetail(route.params.id) */ } catch (e) { console.error(e) } finally { loading.value = false }
})

const handleApprove = () => {
  ElMessage.success('帖子已通过审核')
  router.push('/post')
}

const handleReject = async () => {
  try {
    await ElMessageBox.confirm('确定要拒绝并下架这篇帖子吗？', '拒绝审核', { type: 'warning' })
    ElMessage.success('帖子已下架')
    router.push('/post')
  } catch {}
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要彻底删除这篇帖子吗？此操作不可恢复。', '删除帖子', { type: 'error' })
    ElMessage.success('帖子已删除')
    router.push('/post')
  } catch {}
}
</script>

<template>
  <div v-loading="loading" class="space-y-8">
    <!-- Header -->
    <div class="flex items-center gap-4 animate-float-up">
      <button
        class="flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel-deep text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest hover:scale-[1.02] transition-all"
        @click="router.push('/post')"
      >
        <span class="material-symbols-outlined text-lg">arrow_back</span>
        返回列表
      </button>
    </div>

    <!-- Main Content -->
    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Post Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Post Article -->
        <div class="glass-panel-deep p-8 rounded-3xl depth-2 animate-float-up stagger-1">
          <!-- Post Header -->
          <div class="flex justify-between items-start mb-6">
            <div class="space-y-2">
              <span class="px-3 py-1 bg-primary-container text-on-primary-container rounded-full text-[10px] font-bold tracking-widest uppercase">{{ postData.category }}</span>
              <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold mt-2 leading-tight text-on-surface">{{ postData.title }}</h2>
              <p class="text-sm text-on-surface-variant flex items-center gap-2">
                <span class="material-symbols-outlined text-sm">schedule</span>
                发布于 {{ postData.publishTime }}
              </p>
            </div>
          </div>

          <!-- Post Body -->
          <article class="text-base text-on-surface/90 leading-relaxed space-y-4 mb-8">
            <p v-for="(para, i) in postData.content" :key="i">{{ para }}</p>
          </article>

          <!-- Post Images - Bento Gallery -->
          <div class="grid grid-cols-2 gap-4 h-[400px]">
            <div class="row-span-2 relative group overflow-hidden rounded-2xl">
              <img :src="postData.images[0]" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
              <div class="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div class="relative group overflow-hidden rounded-2xl">
              <img :src="postData.images[1]" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
              <div class="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div class="relative group overflow-hidden rounded-2xl">
              <img :src="postData.images[2]" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
              <div class="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>
        </div>

        <!-- Statistics Section -->
        <div class="flex gap-4 animate-float-up stagger-2">
          <div class="flex-1 glass-panel p-6 rounded-2xl flex items-center justify-between depth-1">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">favorite</span>
              </div>
              <div>
                <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold">点赞总数</p>
                <p class="font-[Plus_Jakarta_Sans] text-xl font-bold">{{ postData.likes.toLocaleString() }}</p>
              </div>
            </div>
            <span class="text-primary text-xs font-bold">+12%</span>
          </div>
          <div class="flex-1 glass-panel p-6 rounded-2xl flex items-center justify-between depth-1">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center text-secondary">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">chat_bubble</span>
              </div>
              <div>
                <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold">评论数量</p>
                <p class="font-[Plus_Jakarta_Sans] text-xl font-bold">{{ postData.comments.toLocaleString() }}</p>
              </div>
            </div>
            <span class="text-secondary text-xs font-bold">+5%</span>
          </div>
          <div class="flex-1 glass-panel p-6 rounded-2xl flex items-center justify-between depth-1">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-tertiary/10 flex items-center justify-center text-tertiary">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">visibility</span>
              </div>
              <div>
                <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold">浏览量</p>
                <p class="font-[Plus_Jakarta_Sans] text-xl font-bold">{{ postData.views }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Sidebar -->
      <div class="space-y-6">
        <!-- Author Card -->
        <div class="glass-panel-deep p-8 rounded-3xl overflow-hidden relative depth-2 animate-float-up stagger-2">
          <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16 blur-2xl" />
          <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-6">作者信息</h3>
          <div class="flex flex-col items-center text-center relative z-10">
            <div class="relative">
              <div class="w-24 h-24 rounded-full border-4 border-white shadow-xl bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-3xl font-bold font-[Plus_Jakarta_Sans]">
                {{ postData.author.name.charAt(0) }}
              </div>
              <span class="absolute bottom-1 right-1 w-6 h-6 bg-primary border-2 border-white rounded-full flex items-center justify-center text-[10px] text-white">✓</span>
            </div>
            <h4 class="font-[Plus_Jakarta_Sans] text-xl font-bold mt-4 mb-1">{{ postData.author.name }}</h4>
            <p class="text-sm text-slate-500 mb-4 px-4">{{ postData.author.bio }}</p>
            <div class="grid grid-cols-2 w-full gap-2 mb-6">
              <div class="bg-white/30 p-3 rounded-xl">
                <p class="text-xs text-slate-400">关注者</p>
                <p class="font-bold text-on-surface">{{ postData.author.followers }}</p>
              </div>
              <div class="bg-white/30 p-3 rounded-xl">
                <p class="text-xs text-slate-400">获赞</p>
                <p class="font-bold text-on-surface">{{ postData.author.totalLikes }}</p>
              </div>
            </div>
            <button @click="router.push({ path: '/post', query: { author: postData.author.name } })" class="w-full py-3 rounded-xl bg-white border border-primary/20 text-primary font-bold hover:bg-primary/5 transition-all">
              查看所有帖子
            </button>
          </div>
        </div>

        <!-- Admin Action Card -->
        <div class="glass-panel-deep p-8 rounded-3xl space-y-4 depth-2 animate-float-up stagger-3">
          <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">审核控制台</h3>
          <div class="p-4 bg-white/20 rounded-2xl border border-white/40">
            <div class="flex items-center gap-3 mb-2">
              <span class="material-symbols-outlined text-amber-500">info</span>
              <span class="font-bold text-sm">当前状态：待审核</span>
            </div>
            <p class="text-[11px] text-slate-600">{{ auditNote }}</p>
          </div>
          <div class="space-y-3 pt-4">
            <button
              class="w-full py-4 rounded-2xl bg-primary text-white font-bold flex items-center justify-center gap-2 shadow-lg shadow-primary/20 hover:scale-[1.02] transition-all btn-jelly"
              @click="handleApprove"
            >
              <span class="material-symbols-outlined">check_circle</span>
              通过审核
            </button>
            <button
              class="w-full py-4 rounded-2xl bg-white border border-tertiary/30 text-tertiary font-bold flex items-center justify-center gap-2 hover:bg-tertiary/5 transition-all"
              @click="handleReject"
            >
              <span class="material-symbols-outlined">block</span>
              拒绝并下架
            </button>
            <div class="h-px bg-white/30 my-4" />
            <button
              class="w-full py-4 rounded-2xl border-2 border-dashed border-error/30 text-error font-bold flex items-center justify-center gap-2 hover:bg-error/5 transition-all"
              @click="handleDelete"
            >
              <span class="material-symbols-outlined">delete</span>
              彻底删除此帖
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
