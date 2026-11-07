<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getAdminMemory,
  getAdminSessionDetail,
  type AdminMemory,
  type AdminSessionDetail,
} from '@/api/agent'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const errorText = ref('')
const detail = ref<AdminSessionDetail | null>(null)
const memory = ref<AdminMemory | null>(null)

const sessionId = computed(() => String(route.params.id || ''))

const totalTokens = computed(() =>
  (detail.value?.runs || []).reduce((sum, run) => sum + run.total_tokens, 0),
)

function roleLabel(role: string): string {
  if (role === 'user') return '用户'
  if (role === 'assistant') return 'Lumina'
  return role
}

function statusType(status: string): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 'succeeded') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running') return 'warning'
  return 'info'
}

async function load() {
  loading.value = true
  errorText.value = ''
  try {
    detail.value = await getAdminSessionDetail(sessionId.value)
    try {
      memory.value = await getAdminMemory(
        detail.value.session.user_id,
        detail.value.session.pet_id,
      )
    } catch {
      // 记忆是附加信息，取不到不影响看对话
      memory.value = null
    }
  } catch (error) {
    errorText.value = (error as Error).message
    ElMessage.error(errorText.value)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <el-button circle @click="router.back()">
        <span class="material-symbols-outlined">arrow_back</span>
      </el-button>
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary">会话详情</h2>
        <p class="text-sm text-on-surface-variant break-all">{{ sessionId }}</p>
      </div>
    </div>

    <el-alert v-if="errorText" :title="errorText" type="error" :closable="false" show-icon />

    <div v-loading="loading" class="space-y-6">
      <template v-if="detail">
        <div class="glass-panel rounded-2xl p-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <p class="text-xs text-on-surface-variant mb-1">用户 ID</p>
            <p class="font-bold">{{ detail.session.user_id }}</p>
          </div>
          <div>
            <p class="text-xs text-on-surface-variant mb-1">宠物 ID</p>
            <p class="font-bold">{{ detail.session.pet_id || '未指定' }}</p>
          </div>
          <div>
            <p class="text-xs text-on-surface-variant mb-1">消息数</p>
            <p class="font-bold">{{ detail.session.message_count }}</p>
          </div>
          <div>
            <p class="text-xs text-on-surface-variant mb-1">累计 token</p>
            <p class="font-bold">{{ totalTokens.toLocaleString() }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <!-- 对话流 -->
          <div class="glass-panel rounded-2xl p-6">
            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">chat</span>
              对话流
            </h3>
            <el-empty v-if="!detail.messages.length" description="没有消息" />
            <div v-else class="space-y-4 max-h-[560px] overflow-y-auto pr-1">
              <div
                v-for="message in detail.messages"
                :key="message.id"
                class="rounded-2xl p-4"
                :class="message.role === 'user' ? 'bg-primary-container/15' : 'bg-white/60'"
              >
                <div class="flex items-center gap-2 mb-2">
                  <el-tag size="small" :type="message.role === 'user' ? 'info' : 'success'">
                    {{ roleLabel(message.role) }}
                  </el-tag>
                  <span class="text-xs text-on-surface-variant">{{ message.create_time }}</span>
                  <span v-if="message.run_id" class="text-xs text-on-surface-variant ml-auto">
                    run {{ message.run_id }}
                  </span>
                </div>
                <p class="text-sm whitespace-pre-wrap break-words">{{ message.content }}</p>
                <div v-if="message.citations.length" class="mt-3 flex flex-wrap gap-2">
                  <el-tag
                    v-for="citation in message.citations"
                    :key="`${citation.kind}-${citation.id}`"
                    size="small"
                    type="warning"
                    effect="plain"
                  >
                    引用 {{ citation.label || citation.kind }} · {{ citation.id }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <!-- 运行轨迹 -->
          <div class="glass-panel rounded-2xl p-6">
            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">route</span>
              运行轨迹
            </h3>
            <el-empty v-if="!detail.runs.length" description="没有运行记录" />
            <el-collapse v-else>
              <el-collapse-item v-for="(run, index) in detail.runs" :key="run.id" :name="run.id">
                <template #title>
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-bold">#{{ index + 1 }} {{ run.route }}</span>
                    <el-tag size="small" :type="statusType(run.status)">{{ run.status }}</el-tag>
                    <span class="text-xs text-on-surface-variant">
                      {{ run.total_tokens }} tokens · {{ run.latency_ms }} ms
                    </span>
                  </div>
                </template>
                <p class="text-xs text-on-surface-variant break-all mb-3">run {{ run.id }}</p>
                <el-alert
                  v-if="run.error"
                  :title="run.error"
                  type="error"
                  :closable="false"
                  class="mb-3"
                />
                <el-timeline>
                  <el-timeline-item
                    v-for="step in run.steps"
                    :key="step.seq"
                    :timestamp="`#${step.seq} ${step.latency_ms} ms`"
                    :type="step.status === 'ok' ? 'primary' : 'danger'"
                  >
                    <span class="text-sm font-medium">{{ step.kind }}</span>
                    <span class="text-sm text-on-surface-variant"> · {{ step.name }}</span>
                    <p v-if="step.error" class="text-xs text-red-500 mt-1">{{ step.error }}</p>
                  </el-timeline-item>
                </el-timeline>
                <el-empty v-if="!run.steps.length" description="这次运行没有落步骤" :image-size="60" />
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <!-- 长期记忆 -->
        <div class="glass-panel rounded-2xl p-6">
          <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">psychology</span>
            这个账号的长期记忆
          </h3>
          <el-empty
            v-if="!memory || !memory.facts.length"
            description="还没有抽取到事实（用户说出名字/过敏/体重等才会记住）"
            :image-size="80"
          />
          <el-table v-else :data="memory.facts">
            <el-table-column prop="label" label="字段" width="120" />
            <el-table-column prop="value" label="值" min-width="180" />
            <el-table-column prop="confidence" label="置信度" width="120" />
            <el-table-column prop="update_time" label="更新时间" width="200" />
          </el-table>
        </div>
      </template>
    </div>
  </div>
</template>
