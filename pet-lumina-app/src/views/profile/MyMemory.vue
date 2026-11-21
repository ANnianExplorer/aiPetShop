<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'
import { deleteMemoryFact, exportMemory, fetchMemoryFacts, AgentRequestError } from '@/api/agent'
import { translateAgentError } from '@/utils/agentError'
import { downloadTextFile } from '@/utils/download'
import {
  buildMemoryExport,
  confidenceLevel,
  filterMemoryRows,
  memoryExportFilename,
  mergeMemoryFacts,
  type MemoryRow,
  type MemoryScope,
} from '@/utils/memoryScope'

const router = useRouter()
const { t } = useI18n()
const { showToast } = useToast()
const userStore = useUserStore()

/** 查询范围：通用 + 每只宠物（后端 pet_id 为空不是「全部」，只能逐个拉） */
const scopes = computed<MemoryScope[]>(() => [
  { petId: null, petName: t('memory.scopeGeneral') },
  ...userStore.pets.map(pet => ({ petId: pet.id, petName: pet.name })),
])

interface ScopeChip {
  key: string
  label: string
  filter: string | null
}

const rows = ref<MemoryRow[]>([])
const loading = ref(true)
const loadError = ref('')
const failedScopes = ref(0)
const activeFilter = ref<string | null>('all')
const pendingDelete = ref<MemoryRow | null>(null)
const deleting = ref(false)
const exporting = ref(false)

const scopeChips = computed<ScopeChip[]>(() => [
  { key: 'all', label: t('memory.scopeAll'), filter: 'all' },
  ...scopes.value.map(scope => ({
    key: scopeKey(scope.petId),
    label: scope.petName,
    filter: scope.petId,
  })),
])

const scopeCounts = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {}
  for (const scope of scopes.value) counts[scopeKey(scope.petId)] = 0
  for (const row of rows.value) {
    const key = scopeKey(row.petId)
    counts[key] = (counts[key] ?? 0) + 1
  }
  return counts
})

const visibleRows = computed(() => filterMemoryRows(rows.value, activeFilter.value))

function scopeKey(petId: string | null): string {
  return petId ?? 'general'
}

function isFulfilled<T>(result: PromiseSettledResult<T>): result is PromiseFulfilledResult<T> {
  return result.status === 'fulfilled'
}

function isRejected(result: PromiseSettledResult<unknown>): result is PromiseRejectedResult {
  return result.status === 'rejected'
}

function reasonText(reason: unknown): string {
  if (reason instanceof AgentRequestError) {
    return translateAgentError(t, reason.code, reason.message, reason.detail.retry_after_s)
  }
  if (reason instanceof Error && reason.message) return reason.message
  return t('memory.error')
}

function countOf(chip: ScopeChip): number {
  if (chip.filter === 'all') return rows.value.length
  return scopeCounts.value[chip.key] ?? 0
}

function confidenceClass(row: MemoryRow): string {
  switch (confidenceLevel(row.confidence)) {
    case 'high':
      return 'bg-emerald-500'
    case 'medium':
      return 'bg-amber-500'
    default:
      return 'bg-zinc-400'
  }
}

function percent(value: number): number {
  return Math.round(value * 100)
}

/** 时间只展示到分钟：后端是 ISO 字符串，空值不展示 */
function displayTime(value: string | null): string {
  if (!value) return ''
  return value.slice(0, 16).replace('T', ' ')
}

function goBack() {
  router.back()
}

async function loadMemory() {
  loading.value = true
  loadError.value = ''
  failedScopes.value = 0
  const settled = await Promise.allSettled(
    scopes.value.map(async scope => ({ scope, facts: await fetchMemoryFacts(scope.petId) })),
  )
  const fulfilled = settled.filter(isFulfilled).map(result => result.value)
  const rejected = settled.filter(isRejected)
  failedScopes.value = rejected.length
  if (fulfilled.length === 0) {
    rows.value = []
    loadError.value = reasonText(rejected[0]?.reason)
  } else {
    rows.value = mergeMemoryFacts(fulfilled)
  }
  loading.value = false
}

function askDelete(row: MemoryRow) {
  pendingDelete.value = row
}

function cancelDelete() {
  if (!deleting.value) pendingDelete.value = null
}

async function confirmDelete() {
  const row = pendingDelete.value
  if (!row || deleting.value) return
  deleting.value = true
  try {
    await deleteMemoryFact(row.key, row.petId)
    rows.value = rows.value.filter(item => !(item.key === row.key && item.petId === row.petId))
    pendingDelete.value = null
    showToast(t('memory.deleteSuccess'), 'success')
  } catch (error) {
    showToast(`${t('memory.deleteFailed')}：${reasonText(error)}`, 'error')
  } finally {
    deleting.value = false
  }
}

async function handleExport() {
  if (exporting.value || loading.value) return
  exporting.value = true
  try {
    const settled = await Promise.allSettled(
      scopes.value.map(async scope => ({ scope, payload: await exportMemory(scope.petId) })),
    )
    const fulfilled = settled.filter(isFulfilled).map(result => result.value)
    if (fulfilled.length === 0) {
      showToast(t('memory.exportFailed'), 'error')
      return
    }
    const now = new Date()
    const file = buildMemoryExport(fulfilled, now)
    downloadTextFile(memoryExportFilename(now), JSON.stringify(file, null, 2))
    const count = fulfilled.reduce((sum, item) => sum + item.payload.facts.length, 0)
    showToast(t('memory.exportSuccess', { count }), 'success')
    const failed = settled.length - fulfilled.length
    if (failed > 0) showToast(t('memory.partialExport', { count: failed }), 'warning')
  } catch (error) {
    showToast(`${t('memory.exportFailed')}：${reasonText(error)}`, 'error')
  } finally {
    exporting.value = false
  }
}

onMounted(loadMemory)
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button
          @click="goBack"
          :aria-label="t('common.back')"
          class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100"
        >
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">{{ t('memory.title') }}</span>
        <div class="w-10"></div>
      </div>

      <p class="text-xs text-on-surface-variant leading-relaxed mb-4">{{ t('memory.subtitle') }}</p>

      <div class="flex items-center justify-between mb-4">
        <span class="text-sm text-on-surface-variant">{{ t('memory.total', { count: rows.length }) }}</span>
        <button
          @click="handleExport"
          :disabled="exporting || loading"
          class="flex items-center gap-1 px-3 py-2 rounded-xl bg-surface-container text-on-surface text-sm font-label-bold active:scale-95 transition-transform disabled:opacity-50"
        >
          <span class="material-symbols-outlined text-base">download</span>
          {{ exporting ? t('memory.exporting') : t('memory.export') }}
        </button>
      </div>

      <div class="flex gap-2 overflow-x-auto no-scrollbar pb-1 mb-4">
        <button
          v-for="chip in scopeChips"
          :key="chip.key"
          @click="activeFilter = chip.filter"
          class="shrink-0 px-3 py-1.5 rounded-full text-xs transition-colors"
          :class="activeFilter === chip.filter ? 'bg-primary text-white' : 'bg-surface-container-low text-on-surface-variant'"
        >
          {{ chip.label }}
          <span class="ml-1 opacity-70">{{ countOf(chip) }}</span>
        </button>
      </div>

      <div v-if="loading" class="space-y-3" :aria-label="t('memory.loading')">
        <div v-for="index in 3" :key="index" class="bg-surface-container-low rounded-xl p-4 animate-pulse">
          <div class="h-3 w-24 rounded bg-surface-container-high mb-3"></div>
          <div class="h-3 w-48 rounded bg-surface-container-high"></div>
        </div>
      </div>

      <div v-else-if="loadError && rows.length === 0" class="bg-surface-container-low rounded-xl p-6 text-center">
        <p class="text-sm text-on-surface mb-1">{{ t('memory.error') }}</p>
        <p class="text-xs text-on-surface-variant mb-4 break-words">{{ loadError }}</p>
        <button
          @click="loadMemory"
          class="px-4 py-2 rounded-xl bg-primary text-white text-sm font-label-bold active:scale-95 transition-transform"
        >
          {{ t('memory.retry') }}
        </button>
      </div>

      <template v-else>
        <p v-if="failedScopes > 0" class="text-xs text-amber-600 mb-3">
          {{ t('memory.partial', { count: failedScopes }) }}
        </p>

        <div v-if="visibleRows.length === 0" class="bg-surface-container-low rounded-xl p-6 text-center">
          <span class="material-symbols-outlined text-outline text-3xl mb-2">psychology</span>
          <p class="text-sm text-on-surface mb-1">{{ t('memory.empty') }}</p>
          <p class="text-xs text-on-surface-variant">{{ t('memory.emptyHint') }}</p>
        </div>

        <article
          v-for="row in visibleRows"
          :key="`${scopeKey(row.petId)}-${row.key}`"
          class="bg-surface-container-low rounded-xl p-4 mb-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-sm font-label-bold text-on-surface break-words">{{ row.label || row.key }}</p>
              <p class="text-sm text-on-surface-variant mt-1 break-words">{{ row.value }}</p>
            </div>
            <button
              @click="askDelete(row)"
              :aria-label="t('memory.delete')"
              class="shrink-0 p-2 rounded-full text-on-surface-variant hover:bg-surface-container-high active:scale-95 transition-transform"
            >
              <span class="material-symbols-outlined text-base">delete</span>
            </button>
          </div>

          <div class="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3 text-[11px] text-on-surface-variant">
            <span class="px-2 py-0.5 rounded-full bg-surface-container">{{ row.petName }}</span>
            <span>{{ t('memory.confidence', { value: percent(row.confidence) }) }}</span>
            <span v-if="row.update_time">{{ t('memory.updatedAt', { time: displayTime(row.update_time) }) }}</span>
          </div>

          <div class="mt-2 h-1 rounded-full bg-surface-container overflow-hidden">
            <div class="h-full rounded-full" :class="confidenceClass(row)" :style="{ width: `${percent(row.confidence)}%` }"></div>
          </div>
        </article>
      </template>
    </main>

    <!-- 删除确认 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="pendingDelete" class="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div class="absolute inset-0 bg-black/40" @click="cancelDelete"></div>
          <div class="relative w-full max-w-sm bg-surface-container-low rounded-3xl p-6 animate-scale-in z-10">
            <h3 class="font-title-sm text-title-sm text-on-surface mb-2">{{ t('memory.deleteTitle') }}</h3>
            <p class="text-sm text-on-surface-variant leading-relaxed">
              {{ t('memory.deleteConfirm', { label: pendingDelete?.label || pendingDelete?.key }) }}
            </p>
            <p class="text-xs text-on-surface-variant/80 mt-2">{{ t('memory.deleteHint') }}</p>
            <div class="flex gap-3 mt-6">
              <button
                @click="cancelDelete"
                :disabled="deleting"
                class="flex-1 py-3 rounded-xl bg-surface-container text-on-surface text-sm font-label-bold active:scale-95 transition-transform disabled:opacity-50"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                @click="confirmDelete"
                :disabled="deleting"
                class="flex-1 py-3 rounded-xl bg-red-500 text-white text-sm font-label-bold active:scale-95 transition-transform disabled:opacity-50"
              >
                {{ deleting ? t('memory.deleting') : t('common.delete') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
