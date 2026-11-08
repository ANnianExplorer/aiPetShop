<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { getAdminTasks, replayDeadLetter, type AdminTasks } from '@/api/agent'

const loading = ref(false)
const replaying = ref('')
const data = ref<AdminTasks | null>(null)

const cards = computed(() => {
  if (!data.value) return []
  return [
    { label: '队列状态', value: data.value.enabled ? '运行中' : '未启用', hint: data.value.backend },
    { label: '已消费', value: data.value.processed.toLocaleString(), hint: '本次进程启动后' },
    { label: '失败次数', value: data.value.failed.toLocaleString(), hint: '含重试，不一定是死信' },
    {
      label: '死信总数',
      value: data.value.topics.reduce((sum, t) => sum + t.dead_letters, 0).toLocaleString(),
      hint: '需要人看，不是垃圾桶',
    },
  ]
})

const hasDeadLetter = computed(() => (data.value?.topics ?? []).some((t) => t.dead_letters > 0))

async function load() {
  loading.value = true
  try {
    data.value = await getAdminTasks()
  } catch (error) {
    ElMessage.error((error as Error).message)
    data.value = null
  } finally {
    loading.value = false
  }
}

async function replay(topic: string, deadLetters: number) {
  try {
    await ElMessageBox.confirm(
      `把「${topic}」里的死信放回队列重试（最多 10 条，attempt 重置为 1）。确认下游已经修好了？`,
      '重放死信',
      { type: 'warning', confirmButtonText: '确认重放', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  replaying.value = topic
  try {
    const result = await replayDeadLetter(topic, Math.min(deadLetters, 10))
    ElMessage.success(`已重放 ${result.replayed} 条，稍后刷新看消费结果`)
    await load()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    replaying.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="队列运维"
      subtitle="旁路队列的现场：剩多少没消费、死信堆了多少；死信是「该被看见」的东西，不是垃圾桶"
      icon="queue"
    />

    <div v-if="data" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="card in cards" :key="card.label" class="glass-panel rounded-2xl p-5">
        <p class="text-xs text-on-surface-variant mb-1">{{ card.label }}</p>
        <p class="text-2xl font-bold text-primary">{{ card.value }}</p>
        <p class="text-[11px] text-on-surface-variant mt-1">{{ card.hint }}</p>
      </div>
    </div>

    <div class="glass-panel rounded-2xl p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold text-on-surface">按 topic 分布</h3>
          <p class="text-xs text-on-surface-variant mt-1">
            积压长期不降说明消费者卡住或下游变慢；死信出现说明重试也没救回来
          </p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>

      <el-alert
        v-if="data && !data.enabled"
        type="info"
        :closable="false"
        show-icon
        title="任务队列未启用（TASK_BACKEND=off）"
        description="当前所有旁路任务都在请求路径里同步执行。要在这里看到队列现场，把后端环境变量切成 memory 或 redis。"
      />

      <el-table v-else :data="data?.topics ?? []" v-loading="loading" row-key="topic">
        <el-table-column prop="topic" label="Topic" min-width="240" />
        <el-table-column prop="depth" label="待消费" width="120">
          <template #default="{ row }">
            <el-tag :type="row.depth > 100 ? 'warning' : 'info'" effect="plain">{{ row.depth }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dead_letters" label="死信" width="120">
          <template #default="{ row }">
            <el-tag :type="row.dead_letters > 0 ? 'danger' : 'success'" effect="plain">
              {{ row.dead_letters }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :disabled="row.dead_letters === 0"
              :loading="replaying === row.topic"
              @click="replay(row.topic, row.dead_letters)"
            >
              重放死信
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有队列数据" />
        </template>
      </el-table>

      <p v-if="data && !hasDeadLetter && data.enabled" class="text-xs text-on-surface-variant mt-4">
        当前没有死信。重试到上限的消息会进死信，处理完之后在这里手动放回。
      </p>
    </div>
  </div>
</template>
