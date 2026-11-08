<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import {
  deleteAdminMemory,
  getAdminMemory,
  type AdminMemory,
  type AdminMemoryFact,
} from '@/api/agent'

const userId = ref('')
const petId = ref('')
const loading = ref(false)
const removing = ref('')
const memory = ref<AdminMemory | null>(null)
const searched = ref(false)

async function load() {
  const uid = userId.value.trim()
  if (!uid) {
    ElMessage.warning('先填用户 ID（会话工作台里能查到）')
    return
  }
  loading.value = true
  try {
    memory.value = await getAdminMemory(uid, petId.value.trim() || null)
    searched.value = true
  } catch (error) {
    ElMessage.error((error as Error).message)
    memory.value = null
    searched.value = false
  } finally {
    loading.value = false
  }
}

async function remove(fact: AdminMemoryFact) {
  try {
    await ElMessageBox.confirm(
      `删除「${fact.label}：${fact.value}」？这是物理删除，删完不可恢复（需要留底请先让用户在 App 里导出）。`,
      '删除记忆',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  removing.value = fact.key
  try {
    await deleteAdminMemory({
      userId: userId.value.trim(),
      key: fact.key,
      petId: petId.value.trim() || null,
    })
    ElMessage.success('已删除；下一轮对话不会再带着它')
    await load()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    removing.value = ''
  }
}

onMounted(() => {
  // 首次进入不自动查：用户 ID 是必填的，空查询只会得到 422
})
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="长期记忆"
      subtitle="用户说过什么、被抽成了什么事实：抽错了在这里删掉，客服不用改代码"
      icon="psychology"
    />

    <div class="glass-panel rounded-2xl p-6">
      <div class="flex flex-wrap items-end gap-4">
        <div>
          <label class="block text-xs text-on-surface-variant mb-1">用户 ID（必填）</label>
          <el-input
            v-model="userId"
            placeholder="如 1001"
            clearable
            style="width: 200px"
            @keyup.enter="load"
          />
        </div>
        <div>
          <label class="block text-xs text-on-surface-variant mb-1">宠物 ID（可选）</label>
          <el-input v-model="petId" placeholder="不填 = 与该用户无关的通用事实" clearable style="width: 260px" />
        </div>
        <el-button type="primary" :loading="loading" @click="load">查询</el-button>
        <span class="ml-auto text-xs text-on-surface-variant">
          共 {{ memory?.facts.length ?? 0 }} 条
        </span>
      </div>

      <el-alert
        class="mt-4"
        type="info"
        :closable="false"
        show-icon
        title="记忆是怎么来的"
        description="对话结束后由旁路任务从用户原话里抽事实（名字/年龄/体重/过敏/忌口/爱吃/疫苗），低置信度不会召回。删除是物理删除。"
      />
    </div>

    <div class="glass-panel rounded-2xl p-6">
      <el-table :data="memory?.facts ?? []" v-loading="loading" row-key="key">
        <el-table-column prop="label" label="类型" width="140" />
        <el-table-column prop="value" label="内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="confidence" label="置信度" width="120">
          <template #default="{ row }">
            <el-tag :type="row.confidence >= 0.9 ? 'success' : 'warning'" effect="plain">
              {{ row.confidence.toFixed(2) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="update_time" label="最近更新" width="200" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              link
              type="danger"
              :loading="removing === row.key"
              @click="remove(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty
            :description="searched ? '这个账号还没有被抽取出记忆' : '填用户 ID 后查询'"
          />
        </template>
      </el-table>
    </div>
  </div>
</template>
