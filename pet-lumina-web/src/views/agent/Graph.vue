<script setup lang="ts">
import { computed, ref } from 'vue'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { theme } from '@/components/charts/echarts'
import { getAdminGraph, type AdminGraph } from '@/api/agent'

const userId = ref('')
const petId = ref('')
const loading = ref(false)
const graph = ref<AdminGraph | null>(null)

const KIND_COLOR: Record<string, string> = {
  pet: '#266a51',
  fact: '#6daf92',
  event: '#91d4b6',
}

const KIND_LABEL: Record<string, string> = { pet: '宠物', fact: '记忆事实', event: '对话事件' }

const summary = computed(() => {
  const nodes = graph.value?.nodes ?? []
  return {
    pet: nodes.filter((n) => n.kind === 'pet').length,
    fact: nodes.filter((n) => n.kind === 'fact').length,
    event: nodes.filter((n) => n.kind === 'event').length,
    edges: graph.value?.edges.length ?? 0,
  }
})

const option = computed(() => {
  const data = graph.value
  if (!data) return {}
  return {
    tooltip: {
      ...theme.tooltip,
      formatter: (params: { dataType?: string; data?: Record<string, unknown> }) => {
        const item = params.data ?? {}
        if (params.dataType === 'edge') return '关系'
        const detail = typeof item.detail === 'string' && item.detail ? `<br/>${item.detail}` : ''
        return `${String(item.label ?? '')}${detail}`
      },
    },
    // 图例不显示颜色分档：本版 ECharts 的 graph 节点实际按 series 单色渲染，
    // 三层用「节点大小 + 标签」区分，避免图例与画面不一致造成误读
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        force: { repulsion: 260, edgeLength: [90, 160], gravity: 0.08 },
        symbol: 'circle',
        // 固定尺寸：早期版本用回调按 kind 计算，实测在 vue-echarts 5 下拿不到 params，
        // 节点退化成 0 尺寸（只剩标签），这里改成常量 + 数据里的 itemStyle 上色
        symbolSize: 46,
        categories: [
          { name: '宠物', itemStyle: { color: KIND_COLOR.pet } },
          { name: '记忆事实', itemStyle: { color: KIND_COLOR.fact } },
          { name: '对话事件', itemStyle: { color: KIND_COLOR.event } },
        ],
        label: {
          show: true,
          position: 'right',
          fontSize: 11,
          fontFamily: theme.bodyFont,
          color: theme.textColor,
          formatter: (params: { data?: Record<string, unknown> }) => String(params.data?.short ?? ''),
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 6,
        edgeLabel: {
          show: true,
          fontSize: 10,
          color: '#8a938e',
          formatter: (params: { data?: Record<string, unknown> }) => String(params.data?.label ?? ''),
        },
        lineStyle: { color: 'rgba(109,175,146,0.45)', width: 1.2, curveness: 0.08 },
        data: data.nodes.map((node) => ({
          id: node.id,
          name: node.id,
          // ECharts 的 symbolSize 回调依赖 data.value 存在；graph 节点默认没有 value，
          // 这里补一个占位值，否则节点会退化成 0 尺寸（只剩标签、没有圆点）
          value: 1,
          label: node.label,
          short: node.label.length > 14 ? `${node.label.slice(0, 13)}…` : node.label,
          detail: node.detail ?? '',
          kind: node.kind,
          category: node.kind === 'pet' ? 0 : node.kind === 'fact' ? 1 : 2,
          // 每个节点单独给尺寸：宠物最大、事实次之、事件最小（series 级 symbolSize 会被这里覆盖）
          symbolSize: node.kind === 'pet' ? 64 : node.kind === 'fact' ? 46 : 34,
        })),
        links: data.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          label: edge.label ?? '',
        })),
      },
    ],
  }
})

async function load() {
  const uid = userId.value.trim()
  if (!uid) {
    ElMessage.warning('先填用户 ID')
    return
  }
  loading.value = true
  try {
    graph.value = await getAdminGraph({
      userId: uid,
      petId: petId.value.trim() || null,
      sessions: 3,
      runsPerSession: 3,
    })
    if (graph.value.nodes.length <= 1) {
      ElMessage.info('这个账号暂时没有记忆事实和对话事件，图里只有宠物节点')
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
    graph.value = null
  } finally {
    loading.value = false
  }
}

function reset() {
  userId.value = ''
  petId.value = ''
  graph.value = null
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="知识图谱"
      subtitle="宠物为中心的三层视图：宠物 — 记忆事实 — 最近对话事件；只画 Agent 自己库里的数据"
      icon="hub"
    />

    <div class="glass-panel rounded-2xl p-6">
      <div class="flex flex-wrap items-end gap-4">
        <div>
          <label class="block text-xs text-on-surface-variant mb-1">用户 ID（必填）</label>
          <el-input v-model="userId" placeholder="如 1001" clearable style="width: 200px" @keyup.enter="load" />
        </div>
        <div>
          <label class="block text-xs text-on-surface-variant mb-1">宠物 ID（可选）</label>
          <el-input v-model="petId" placeholder="不填 = 该用户全部宠物" clearable style="width: 220px" />
        </div>
        <el-button type="primary" :loading="loading" @click="load">生成图谱</el-button>
        <el-button @click="reset">清空</el-button>
        <div class="ml-auto flex gap-4 text-xs text-on-surface-variant">
          <span>宠物 {{ summary.pet }}</span>
          <span>事实 {{ summary.fact }}</span>
          <span>事件 {{ summary.event }}</span>
          <span>边 {{ summary.edges }}</span>
        </div>
      </div>
    </div>

    <div class="glass-panel rounded-2xl p-4">
      <div v-if="graph" v-loading="loading" class="h-[520px]">
        <v-chart :option="option" autoresize style="height: 100%; width: 100%" />
        <p class="text-[11px] text-on-surface-variant px-4">
          拖拽节点可调整布局；滚轮缩放。事实来自 `memory_fact`，事件来自最近的 `agent_run`（最多 3 个会话 × 每个 3 轮）。
        </p>
      </div>
      <el-empty v-else description="填用户 ID 后生成图谱" class="py-20" />
    </div>
  </div>
</template>
