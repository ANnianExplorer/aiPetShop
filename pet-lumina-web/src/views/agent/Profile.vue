<script setup lang="ts">
/**
 * 宠物画像：把「这只宠物被系统记住了什么」摆给运营看。
 *
 * 三条展示原则：
 * 1. 只展示结构化结论，不展示模型生成的散文（画像是规则聚合的产物）；
 * 2. 每条风险/待办都要能点开看到证据来源（factId + 置信度）；
 * 3. `stale` 用显式提示，不假装实时——重算由用户的下一轮对话触发。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { getAdminProfile, getAdminProfileVersions } from '@/api/agent'
import type { AdminProfile } from '@/api/agent'

const userId = ref('')
const petId = ref('')
const loading = ref(false)
const searched = ref(false)
const profile = ref<AdminProfile | null>(null)
const versions = ref<AdminProfile[]>([])
const emptyHint = ref('')

const evidence = computed(() => profile.value?.data?.evidence ?? [])
const risks = computed(() => profile.value?.data?.riskFlags ?? [])
const gaps = computed(() => profile.value?.data?.careGaps ?? [])
const prefs = computed(() => profile.value?.data?.preferences ?? [])
const basics = computed(() => {
  const raw = profile.value?.data?.basics ?? {}
  const labels: Record<string, string> = { name: '名字', age: '年龄', weightKg: '体重(kg)', weightText: '体重(原文)' }
  return Object.entries(raw).map(([key, value]) => ({ label: labels[key] ?? key, value: String(value) }))
})

async function load() {
  const uid = userId.value.trim()
  if (!uid) {
    ElMessage.warning('先填用户 ID')
    return
  }
  loading.value = true
  emptyHint.value = ''
  try {
    const data = await getAdminProfile({ userId: uid, petId: petId.value.trim() || null })
    profile.value = data
    versions.value = []
    // 版本历史是加分项：拿不到不影响主视图
    getAdminProfileVersions({ userId: uid, petId: petId.value.trim() || null, limit: 5 })
      .then((resp) => (versions.value = resp.items))
      .catch(() => (versions.value = []))
  } catch (err) {
    const error = err as { status?: number; message?: string }
    profile.value = null
    versions.value = []
    emptyHint.value =
      error.status === 404
        ? '该账号还没有画像：等用户聊过一轮，或让用户在自己的 App 里点「重算画像」'
        : error.message || '画像加载失败'
  } finally {
    loading.value = false
    searched.value = true
  }
}

function reset() {
  userId.value = ''
  petId.value = ''
  profile.value = null
  versions.value = []
  emptyHint.value = ''
  searched.value = false
}

onMounted(() => {
  // 画像页通常从用户列表跳过来，允许 URL 带 user_id
  const query = new URLSearchParams(window.location.hash.split('?')[1] ?? '')
  const preset = query.get('user_id')
  if (preset) {
    userId.value = preset
    void load()
  }
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="宠物画像"
      subtitle="由已确认的记忆事实确定性聚合：每条结论都能回放到一条事实"
    />

    <section class="glass-panel rounded-3xl p-5">
      <div class="flex flex-wrap items-end gap-4">
        <label class="flex flex-col gap-1 text-sm text-on-surface-variant">
          用户 ID（必填）
          <el-input v-model="userId" placeholder="如 1001" class="!w-56" clearable @keyup.enter="load" />
        </label>
        <label class="flex flex-col gap-1 text-sm text-on-surface-variant">
          宠物 ID（可选）
          <el-input v-model="petId" placeholder="不填 = 该用户全部宠物" class="!w-64" clearable />
        </label>
        <el-button type="primary" :loading="loading" @click="load">查询画像</el-button>
        <el-button @click="reset">重置</el-button>
        <span v-if="profile" class="ml-auto text-sm text-on-surface-variant">
          版本 v{{ profile.version }} · 事实 {{ profile.fact_count }} 条 · 置信度 {{ profile.confidence.toFixed(2) }}
        </span>
      </div>
      <p class="mt-3 text-xs text-on-surface-variant">
        画像是「事实的当前快照」：用户每轮对话后由旁路任务重算一版，只保留最近 20 版。
        事实更新后这里会标记「有更新」，等下一轮对话或用户主动重算即可刷新。
      </p>
    </section>

    <section v-if="profile" class="space-y-4">
      <div v-if="profile.stale" class="rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
        事实比这份画像新，摘要可能落后；等用户下一轮对话或让用户在 App 里点「重算画像」。
      </div>

      <div class="grid gap-4 lg:grid-cols-3">
        <el-card shadow="never" class="rounded-2xl">
          <template #header><span class="font-medium">基础信息</span></template>
          <div v-if="basics.length" class="space-y-2 text-sm">
            <div v-for="item in basics" :key="item.label" class="flex justify-between gap-4">
              <span class="text-on-surface-variant">{{ item.label }}</span>
              <span class="font-medium">{{ item.value }}</span>
            </div>
          </div>
          <el-empty v-else description="还没有基础信息（名字/年龄/体重）" :image-size="60" />
        </el-card>

        <el-card shadow="never" class="rounded-2xl">
          <template #header><span class="font-medium">风险</span></template>
          <ul v-if="risks.length" class="space-y-2 text-sm">
            <li v-for="(item, index) in risks" :key="index" class="rounded-xl bg-rose-50 px-3 py-2 text-rose-700">
              {{ item.text }}
            </li>
          </ul>
          <p v-else class="text-sm text-on-surface-variant">没有已知风险（过敏等）</p>
        </el-card>

        <el-card shadow="never" class="rounded-2xl">
          <template #header><span class="font-medium">待办</span></template>
          <ul v-if="gaps.length" class="space-y-2 text-sm">
            <li v-for="(item, index) in gaps" :key="index" class="rounded-xl bg-amber-50 px-3 py-2 text-amber-700">
              {{ item.text }}
            </li>
          </ul>
          <p v-else class="text-sm text-on-surface-variant">没有需要提醒的待办</p>
        </el-card>
      </div>

      <el-card shadow="never" class="rounded-2xl">
        <template #header><span class="font-medium">偏好</span></template>
        <div v-if="prefs.length" class="flex flex-wrap gap-2">
          <el-tag v-for="(item, index) in prefs" :key="index" type="success" effect="plain">
            {{ item.text }}
          </el-tag>
        </div>
        <p v-else class="text-sm text-on-surface-variant">还没有记录饮食偏好</p>
      </el-card>

      <el-card shadow="never" class="rounded-2xl">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-medium">证据（{{ evidence.length }}）</span>
            <span class="text-xs text-on-surface-variant">画像只由这些事实生成，删掉事实后下一版就会消失</span>
          </div>
        </template>
        <el-table :data="evidence" size="small" empty-text="没有事实支撑">
          <el-table-column prop="key" label="字段" width="140" />
          <el-table-column prop="value" label="值" />
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="{ row }">
              <el-tag :type="row.confidence >= 0.9 ? 'success' : 'warning'" effect="plain">
                {{ row.confidence.toFixed(2) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="factId" label="事实 ID" width="200" />
        </el-table>
      </el-card>

      <el-card v-if="versions.length > 1" shadow="never" class="rounded-2xl">
        <template #header><span class="font-medium">版本历史</span></template>
        <el-table :data="versions" size="small">
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="fact_count" label="事实数" width="100" />
          <el-table-column prop="confidence" label="置信度" width="100" />
          <el-table-column prop="create_time" label="生成时间" />
        </el-table>
      </el-card>
    </section>

    <section v-else-if="searched" class="glass-panel rounded-3xl p-10 text-center text-sm text-on-surface-variant">
      {{ emptyHint || '没有画像数据' }}
    </section>
  </div>
</template>
