<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getAdminModelConfig,
  saveAdminModelConfig,
  testAdminModelConfig,
  type AdminModelConfig,
} from '@/api/agent'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

interface ModelForm {
  provider: string
  base_url: string
  model: string
  api_key: string
  enabled: boolean
}

const config = ref<AdminModelConfig | null>(null)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const loadError = ref('')
const form = reactive<ModelForm>({
  provider: '',
  base_url: '',
  model: '',
  api_key: '',
  enabled: false,
})

const providerOptions = ['deepseek', 'openai', 'openai-compatible', 'custom']

const sourceLabel = computed(() => {
  if (!config.value) return '未加载'
  return config.value.source === 'db' ? '数据库配置' : config.value.source === 'env' ? '环境变量兜底' : '未配置'
})

const sourceTag = computed<TagType>(() => {
  if (!config.value) return 'info'
  return config.value.source === 'db' ? 'success' : config.value.source === 'env' ? 'warning' : 'info'
})

const runtimeLabel = computed(() => {
  if (!config.value) return '未知'
  if (!config.value.runtime_model) return '未加载模型'
  return `${config.value.runtime_model}（${config.value.runtime_source === 'db' ? '数据库' : config.value.runtime_source === 'env' ? '环境变量' : '注入'}）`
})

const keyPlaceholder = computed(() =>
  config.value?.source === 'db' && config.value.has_api_key
    ? `已保存 ${config.value.api_key_masked}，留空沿用`
    : 'sk-...（启用时必须填写）',
)

function fillForm(data: AdminModelConfig): void {
  config.value = data
  form.provider = data.provider || 'deepseek'
  form.base_url = data.base_url || ''
  form.model = data.model || ''
  form.api_key = ''
  form.enabled = data.enabled
}

async function load(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    fillForm(await getAdminModelConfig())
  } catch (error) {
    loadError.value = (error as Error).message
  } finally {
    loading.value = false
  }
}

function validate(): string | null {
  if (!form.provider.trim()) return '请选择或填写提供方'
  if (!/^https?:\/\//.test(form.base_url.trim())) return 'Base URL 必须以 http:// 或 https:// 开头'
  if (!form.model.trim()) return '请填写模型 ID'
  const hasSavedDbKey = config.value?.source === 'db' && config.value.has_api_key
  if (form.enabled && !form.api_key.trim() && !hasSavedDbKey) {
    return '启用数据库配置必须填写 API Key'
  }
  return null
}

async function testConnection(): Promise<void> {
  const problem = validate()
  if (problem) {
    ElMessage.warning(problem)
    return
  }
  testing.value = true
  try {
    const result = await testAdminModelConfig({
      provider: form.provider.trim(),
      base_url: form.base_url.trim(),
      model: form.model.trim(),
      api_key: form.api_key.trim(),
      enabled: form.enabled,
    })
    ElMessage.success(`连接成功：${result.model}，${result.latency_ms} ms`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    testing.value = false
  }
}

async function save(): Promise<void> {
  const problem = validate()
  if (problem) {
    ElMessage.warning(problem)
    return
  }
  saving.value = true
  try {
    const data = await saveAdminModelConfig({
      provider: form.provider.trim(),
      base_url: form.base_url.trim(),
      model: form.model.trim(),
      api_key: form.api_key.trim(),
      enabled: form.enabled,
    })
    fillForm(data)
    ElMessage.success(data.enabled ? '配置已保存并热应用' : '已禁用数据库配置，运行时回退环境变量')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6 animate-float-up" data-testid="model-config-page">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <div class="flex items-center gap-3">
          <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">模型配置</h2>
          <el-tag :type="sourceTag" effect="light">{{ sourceLabel }}</el-tag>
        </div>
        <p class="mt-2 max-w-3xl text-sm text-on-surface-variant">
          管理员统一配置对话模型。保存后立即热应用到 Agent，无需重启；API Key 只写不读，页面仅显示末四位。
          未配置或禁用数据库配置时，运行时回退环境变量。
        </p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      show-icon
      :closable="false"
    />

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
      <section class="glass-panel rounded-3xl p-6 depth-1">
        <div class="mb-5 flex items-center gap-2">
          <span class="h-5 w-1.5 rounded-full bg-primary" />
          <h3 class="font-[Plus_Jakarta_Sans] text-lg font-bold text-on-surface">连接参数</h3>
        </div>

        <el-form label-position="top" @submit.prevent>
          <el-form-item label="提供方">
            <el-select
              v-model="form.provider"
              allow-create
              filterable
              default-first-option
              placeholder="选择或输入提供方"
              class="w-full"
            >
              <el-option v-for="item in providerOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>

          <el-form-item label="Base URL">
            <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" clearable />
            <p class="mt-1 text-xs text-on-surface-variant">
              填到 OpenAI 兼容接口的版本根路径，系统会拼接 /chat/completions。
            </p>
          </el-form-item>

          <el-form-item label="模型 ID">
            <el-input v-model="form.model" placeholder="deepseek-chat" clearable />
          </el-form-item>

          <el-form-item label="API Key">
            <el-input
              v-model="form.api_key"
              type="password"
              show-password
              autocomplete="new-password"
              :placeholder="keyPlaceholder"
            />
            <p class="mt-1 text-xs text-on-surface-variant">
              加密后写入配置存储；接口和页面都不会返回明文。留空表示沿用已保存的 Key。
            </p>
          </el-form-item>

          <el-form-item label="启用数据库配置">
            <div class="flex items-center gap-3">
              <el-switch v-model="form.enabled" active-color="#6daf92" />
              <span class="text-sm text-on-surface-variant">
                {{ form.enabled ? '保存后立即使用此配置' : '保存后停用，运行时回退环境变量' }}
              </span>
            </div>
          </el-form-item>

          <div class="mt-6 flex flex-wrap gap-3">
            <el-button data-testid="model-config-test" :loading="testing" @click="testConnection">测试连接</el-button>
            <el-button data-testid="model-config-save" type="primary" :loading="saving" @click="save">保存并应用</el-button>
          </div>
        </el-form>
      </section>

      <section class="space-y-6">
        <div class="glass-panel rounded-3xl p-6 depth-1">
          <div class="mb-4 flex items-center gap-2">
            <span class="h-5 w-1.5 rounded-full bg-secondary" />
            <h3 class="font-[Plus_Jakarta_Sans] text-lg font-bold text-on-surface">当前运行时</h3>
          </div>
          <dl class="space-y-3 text-sm">
            <div class="flex items-start justify-between gap-4">
              <dt class="text-on-surface-variant">运行时模型</dt>
              <dd class="text-right font-medium text-on-surface">{{ runtimeLabel }}</dd>
            </div>
            <div class="flex items-start justify-between gap-4">
              <dt class="text-on-surface-variant">配置来源</dt>
              <dd class="text-right font-medium text-on-surface">{{ sourceLabel }}</dd>
            </div>
            <div class="flex items-start justify-between gap-4">
              <dt class="text-on-surface-variant">已保存 Key</dt>
              <dd class="text-right font-mono font-medium text-on-surface">
                {{ config?.has_api_key ? config.api_key_masked : '未保存' }}
              </dd>
            </div>
            <div class="flex items-start justify-between gap-4">
              <dt class="text-on-surface-variant">最近更新</dt>
              <dd class="text-right font-medium text-on-surface">{{ config?.update_time || '—' }}</dd>
            </div>
            <div class="flex items-start justify-between gap-4">
              <dt class="text-on-surface-variant">更新人</dt>
              <dd class="text-right font-medium text-on-surface">{{ config?.updated_by || '—' }}</dd>
            </div>
          </dl>
        </div>

        <el-alert
          v-if="config?.error"
          :title="config.error"
          type="error"
          show-icon
          :closable="false"
        />
        <el-alert
          v-else-if="config?.source === 'db' && !config.enabled && config.fallback === 'env'"
          title="数据库配置已禁用，当前使用环境变量兜底"
          type="warning"
          show-icon
          :closable="false"
        />
        <el-alert
          v-else-if="config?.source === 'none'"
          title="还没有可用模型，填写参数并启用后即可对话"
          type="info"
          show-icon
          :closable="false"
        />

        <div class="glass-panel rounded-3xl border border-white/40 p-5 text-xs leading-relaxed text-on-surface-variant depth-1">
          <p class="mb-2 font-bold text-on-surface">安全与生效说明</p>
          <p>· Key 使用服务端主密钥加密，主密钥来自 PET_AGENT_CONFIG_SECRET 或本地 data/model-config.key。</p>
          <p>· 保存会先构建模型再落库，构建失败不会覆盖旧配置。</p>
          <p>· 热切换只影响新请求，在途对话继续使用旧模型直到结束。</p>
        </div>
      </section>
    </div>
  </div>
</template>
