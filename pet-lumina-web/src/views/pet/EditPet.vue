<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const form = ref({
  name: 'Mochi',
  breed: '金毛寻回犬',
  type: '狗',
  gender: '公',
  age: '3',
  weight: '28.5',
  birthday: '2021-05-12',
  immunizationStatus: '已完成',
  healthNote: '对鸡肉有过敏倾向，建议饮食中避开相关成分。',
})

const photoPreview = ref('')

onMounted(async () => {
  loading.value = true
  try { /* const res = await petApi.getDetail(route.params.id) */ } catch (e) { console.error(e) } finally { loading.value = false }
})

const handleSubmit = () => {
  if (!form.value.name || !form.value.breed) {
    ElMessage.warning('请填写宠物名称和品种')
    return
  }
  ElMessage.success('宠物信息已更新')
  router.push(`/pet/${route.params.id}`)
}
</script>

<template>
  <div class="space-y-8 animate-float-up">
    <!-- Back Button -->
    <div class="flex items-center justify-between">
      <button
        class="flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest hover:scale-105 transition-transform duration-300 group"
        @click="router.back()"
      >
        <span class="material-symbols-outlined text-xl group-hover:-translate-x-1 transition-transform">arrow_back</span>
        返回详情
      </button>
    </div>

    <!-- Edit Form -->
    <div class="flex items-start justify-center pt-4">
      <section class="glass-panel-deep w-full max-w-3xl rounded-3xl p-10 depth-3 relative overflow-hidden">
        <div class="absolute -top-24 -right-24 w-64 h-64 bg-primary-container/10 rounded-full blur-3xl" />

        <div class="relative z-10">
          <div class="mb-10 text-center">
            <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary mb-2">编辑宠物信息</h2>
            <p class="text-sm text-on-surface-variant">修改宠物的基本资料与健康档案</p>
          </div>

          <form class="space-y-8" @submit.prevent="handleSubmit">
            <!-- Avatar Section -->
            <div class="flex flex-col items-center gap-4 mb-8">
              <div class="relative group">
                <div class="w-32 h-32 rounded-3xl border-4 border-white/50 shadow-xl overflow-hidden glass-panel">
                  <div v-if="!photoPreview" class="w-full h-full bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-4xl">
                    <span class="material-symbols-outlined" style="font-size: 48px">pets</span>
                  </div>
                  <img v-else :src="photoPreview" class="w-full h-full object-cover" />
                </div>
                <label class="absolute bottom-0 right-0 w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center cursor-pointer shadow-lg hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-xl">photo_camera</span>
                  <input class="hidden" type="file" />
                </label>
              </div>
              <span class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-primary">点击图标更换照片</span>
            </div>

            <!-- Form Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">宠物名称</label>
                <div class="relative">
                  <span class="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-400">pets</span>
                  <input v-model="form.name" class="glass-input w-full pl-12 pr-4 py-3 rounded-xl text-sm" type="text" />
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">品种</label>
                <el-select v-model="form.breed" style="width: 100%">
                  <el-option label="金毛寻回犬" value="金毛寻回犬" />
                  <el-option label="拉布拉多" value="拉布拉多" />
                  <el-option label="布偶猫" value="布偶猫" />
                  <el-option label="英短蓝猫" value="英短蓝猫" />
                  <el-option label="哈士奇" value="哈士奇" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">年龄 (岁)</label>
                <input v-model="form.age" class="glass-input w-full rounded-xl px-4 py-3 text-sm" type="number" />
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">体重 (kg)</label>
                <input v-model="form.weight" class="glass-input w-full rounded-xl px-4 py-3 text-sm" type="number" step="0.1" />
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">性别</label>
                <div class="flex p-1 bg-white/20 rounded-xl border border-white/10">
                  <label class="flex-1">
                    <input v-model="form.gender" value="公" class="hidden peer" type="radio" name="gender" />
                    <div class="text-center py-2 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">
                      雄性
                    </div>
                  </label>
                  <label class="flex-1">
                    <input v-model="form.gender" value="母" class="hidden peer" type="radio" name="gender" />
                    <div class="text-center py-2 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">
                      雌性
                    </div>
                  </label>
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">生日</label>
                <input v-model="form.birthday" class="glass-input w-full rounded-xl px-4 py-3 text-sm" type="date" />
              </div>
            </div>

            <!-- Health Notes -->
            <div class="space-y-2">
              <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">健康状况描述</label>
              <textarea v-model="form.healthNote" class="glass-input w-full rounded-xl px-4 py-3 text-sm resize-none" rows="4" />
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-4 pt-6">
              <button
                class="px-8 py-3 rounded-xl text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest text-on-surface-variant hover:bg-white/30 transition-all"
                type="button"
                @click="router.back()"
              >
                取消
              </button>
              <button
                class="px-10 py-3 bg-primary text-white rounded-xl text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest shadow-[0_10px_20px_-5px_rgba(38,106,81,0.4)] hover:scale-105 active:scale-95 transition-all duration-300 flex items-center gap-2 btn-jelly"
                type="submit"
              >
                <span class="material-symbols-outlined text-lg">save</span>
                保存修改
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  </div>
</template>
