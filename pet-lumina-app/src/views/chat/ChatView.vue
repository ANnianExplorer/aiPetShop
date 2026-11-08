<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import 'vant/es/toast/style'
import {
  AgentRequestError,
  fetchSessionMessages,
  fetchSessions,
  streamChat,
  uploadDocument,
} from '@/api/agent'
import { applyAgentEvent, historyToBubbles } from '@/utils/chatStream'
import { publishWorkState } from '@/pet/signal'
import { useUserStore } from '@/stores/user'
import type { AgentEvent } from '@/api/agent'
import type { AgentCitation, AgentSessionItem, ChatBubble, ToolEvent } from '@/types/agent'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const SESSION_KEY = 'petlumina-agent-session'

const bubbles = ref<ChatBubble[]>([])
const draft = ref('')
const streaming = ref(false)
const sessionId = ref<string | null>(localStorage.getItem(SESSION_KEY))
const scroller = ref<HTMLElement | null>(null)
const input = ref<HTMLTextAreaElement | null>(null)
const lastError = ref<string>('')
const historyOpen = ref(false)
const historyLoading = ref(false)
const historyError = ref('')
const sessions = ref<AgentSessionItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

let controller: AbortController | null = null
let seqCounter = 0

const petName = computed(() => userStore.currentPet?.name ?? '')
const canSend = computed(() => draft.value.trim().length > 0 && !streaming.value)

const suggestions = computed(() => [
  t('chat.suggest.health'),
  t('chat.suggest.vaccine'),
  t('chat.suggest.food'),
])

const nextId = (prefix: string) => `${prefix}-${Date.now()}-${seqCounter++}`

async function scrollToBottom() {
  await nextTick()
  const el = scroller.value
  if (el) el.scrollTop = el.scrollHeight
}

function rememberSession(id: string) {
  sessionId.value = id
  localStorage.setItem(SESSION_KEY, id)
}

async function loadHistory() {
  if (!sessionId.value) return
  try {
    const history = await fetchSessionMessages(sessionId.value)
    bubbles.value = historyToBubbles(history)
    await scrollToBottom()
  } catch (error) {
    // 会话在服务端已被清理（比如内存模式重启）：换新会话，不打断用户
    if (error instanceof AgentRequestError && (error.code === 'not_found' || error.code === 'http_404')) {
      localStorage.removeItem(SESSION_KEY)
      sessionId.value = null
      return
    }
    showToast(t('chat.historyFailed'))
  }
}

function pickDocument() {
  if (uploading.value) return
  fileInput.value?.click()
}

async function onFilePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  uploading.value = true
  try {
    const doc = await uploadDocument(file, userStore.currentPet ? String(userStore.currentPet.id) : null)
    bubbles.value.push({
      id: nextId('user'),
      role: 'user',
      content: `📄 ${file.name}`,
      citations: [],
      tools: [],
    })
    await scrollToBottom()
    showToast(
      doc.status === 2
        ? t('chat.uploadReady', { name: file.name })
        : t('chat.uploadQueued', { name: file.name }),
    )
  } catch (error) {
    const message = error instanceof AgentRequestError ? error.message : String(error)
    showToast(t('chat.uploadFailed', { reason: message }))
  } finally {
    uploading.value = false
  }
}

function handleEvent(event: AgentEvent, assistant: ChatBubble) {
  // 桌宠联动：一轮对话里「在想 / 在查 / 完成 / 出错」各对应一档动画
  // （route→thinking、tool→working、done→success、error→error），与 dsh-pet 的档位映射同源。
  if (event.event === 'route') publishWorkState('thinking')
  else if (event.event === 'tool') publishWorkState('working')
  else if (event.event === 'done') publishWorkState('success')
  else if (event.event === 'error') publishWorkState('error')
  const outcome = applyAgentEvent(assistant, event)
  if (outcome.sessionId) rememberSession(outcome.sessionId)
  if (outcome.dropBubble) {
    bubbles.value = bubbles.value.filter((b) => b.id !== assistant.id)
  }
  if (outcome.error) {
    lastError.value = outcome.error
  }
  if (event.event === 'delta' || event.event === 'done') {
    void scrollToBottom()
  }
}

async function send(text?: string) {
  const content = (text ?? draft.value).trim()
  if (!content || streaming.value) return

  lastError.value = ''
  draft.value = ''
  bubbles.value.push({ id: nextId('user'), role: 'user', content, citations: [], tools: [] })

  const assistant: ChatBubble = {
    id: nextId('assistant'),
    role: 'assistant',
    content: '',
    citations: [],
    tools: [],
    streaming: true,
  }
  bubbles.value.push(assistant)
  streaming.value = true
  publishWorkState('thinking')
  controller = new AbortController()
  await scrollToBottom()

  try {
    await streamChat(
      {
        message: content,
        sessionId: sessionId.value,
        // 后端 id 是 19 位 BigInteger，前端类型标的是 number：统一转字符串再出网
        petId: userStore.currentPet ? String(userStore.currentPet.id) : null,
      },
      { signal: controller.signal, onEvent: (event) => handleEvent(event, assistant) },
    )
  } catch (error) {
    assistant.streaming = false
    if ((error as Error).name === 'AbortError') return
    if (error instanceof AgentRequestError) {
      if (error.code === 'unauthorized' || error.code === 'http_401') {
        localStorage.removeItem('satoken')
        showToast(t('chat.loginExpired'))
        void router.push('/login')
        return
      }
      lastError.value = error.message
    } else {
      lastError.value = t('chat.sendFailed')
    }
    if (!assistant.content) {
      bubbles.value = bubbles.value.filter((b) => b.id !== assistant.id)
    }
  } finally {
    streaming.value = false
    // 出错或断流时也要把桌宠从「工作中」放出来，否则它会一直忙到下次对话
    if (lastError.value !== '') publishWorkState('error')
    controller = null
    await scrollToBottom()
    input.value?.focus()
  }
}

function retry() {
  const lastUser = [...bubbles.value].reverse().find((b) => b.role === 'user')
  if (lastUser) void send(lastUser.content)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    void send()
  }
}

function openCitation(citation: AgentCitation) {
  if (citation.kind === 'log') {
    void router.push(`/log/${citation.id}`)
    return
  }
  showToast(citation.label)
}

function startNewChat() {
  localStorage.removeItem(SESSION_KEY)
  sessionId.value = null
  bubbles.value = []
  lastError.value = ''
  historyOpen.value = false
}

/** 打开历史面板：每次打开都重新拉，避免显示过期列表 */
async function openHistory() {
  if (streaming.value) {
    showToast(t('chat.thinking'))
    return
  }
  historyOpen.value = true
  historyLoading.value = true
  historyError.value = ''
  try {
    const page = await fetchSessions(1, 20)
    sessions.value = page.items
  } catch (error) {
    if (error instanceof AgentRequestError && (error.code === 'unauthorized' || error.code === 'http_401')) {
      localStorage.removeItem('satoken')
      historyOpen.value = false
      showToast(t('chat.loginExpired'))
      void router.push('/login')
      return
    }
    historyError.value = t('chat.historyLoadFailed')
  } finally {
    historyLoading.value = false
  }
}

/** 切换到某个历史会话：先清空气泡再回读，避免上一条会话的内容串进来 */
function openSession(id: string) {
  historyOpen.value = false
  if (id === sessionId.value) return
  rememberSession(id)
  bubbles.value = []
  lastError.value = ''
  void loadHistory()
}

function formatWhen(value?: string | null): string {
  return value ? value.slice(0, 16) : ''
}

onMounted(() => {
  void loadHistory()
  void scrollToBottom()
})

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background">
    <!-- 顶部：返回 + 身份 + 新会话 -->
    <header class="sticky top-0 z-20 bg-background/80 px-4 pb-3 pt-safe backdrop-blur-xl">
      <div class="flex items-center gap-3 pt-4">
        <button
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-low text-on-surface"
          :aria-label="t('common.back')"
          @click="router.back()"
        >
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <div class="flex flex-1 items-center gap-3">
          <div class="relative flex h-11 w-11 items-center justify-center rounded-full bg-primary/10">
            <span class="material-symbols-outlined text-2xl text-primary">pets</span>
            <span class="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-emerald-500" />
          </div>
          <div class="leading-tight">
            <p class="font-title-md text-on-surface">Lumina</p>
            <p class="text-xs text-on-surface-variant">
              {{ petName ? t('chat.subtitlePet', { name: petName }) : t('chat.subtitle') }}
            </p>
          </div>
        </div>
        <button
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
          :aria-label="t('chat.history')"
          @click="openHistory"
        >
          <span class="material-symbols-outlined">history</span>
        </button>
        <button
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
          :aria-label="t('chat.newChat')"
          @click="startNewChat"
        >
          <span class="material-symbols-outlined">edit_square</span>
        </button>
      </div>
    </header>

    <!-- 消息区 -->
    <main ref="scroller" class="flex-1 space-y-4 overflow-y-auto px-4 pb-40 no-scrollbar">
      <div v-if="bubbles.length === 0" class="mt-10 space-y-6">
        <div class="glass-card rounded-3xl p-6">
          <p class="font-title-md text-on-surface">{{ t('chat.emptyTitle') }}</p>
          <p class="mt-2 text-sm leading-relaxed text-on-surface-variant">
            {{ t('chat.emptyBody') }}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="item in suggestions"
            :key="item"
            class="rounded-full border border-outline-variant/60 px-4 py-2 text-sm text-on-surface-variant active:scale-95"
            @click="send(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>

      <template v-for="bubble in bubbles" :key="bubble.id">
        <div v-if="bubble.role === 'user'" class="flex justify-end">
          <div class="max-w-[78%] rounded-3xl rounded-br-lg bg-primary px-4 py-3 text-sm leading-relaxed text-on-primary">
            {{ bubble.content }}
          </div>
        </div>

        <div v-else class="flex justify-start">
          <div class="max-w-[85%] space-y-2">
            <div class="glass-card rounded-3xl rounded-bl-lg px-4 py-3">
              <p v-if="bubble.content" class="whitespace-pre-wrap text-sm leading-relaxed text-on-surface">
                {{ bubble.content }}<span v-if="bubble.streaming" class="ml-0.5 animate-pulse">▍</span>
              </p>
              <p v-else-if="bubble.streaming" class="text-sm text-on-surface-variant animate-pulse">
                {{ t('chat.thinking') }}
              </p>

              <div v-if="bubble.tools.length" class="mt-2 flex flex-wrap gap-1.5">
                <span
                  v-for="(tool, index) in bubble.tools"
                  :key="`${tool.name}-${index}`"
                  class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2 py-1 text-[11px] text-on-surface-variant"
                >
                  <span class="material-symbols-outlined text-[13px]">travel_explore</span>
                  {{ t(`chat.tool.${tool.name}`, tool.name) }}
                </span>
              </div>

              <div v-if="bubble.citations.length" class="mt-3 flex flex-wrap gap-1.5 border-t border-outline-variant/40 pt-2">
                <button
                  v-for="citation in bubble.citations"
                  :key="`${citation.kind}-${citation.id}`"
                  class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-[11px] text-primary active:scale-95"
                  @click="openCitation(citation)"
                >
                  <span class="material-symbols-outlined text-[13px]">link</span>
                  {{ citation.label }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="lastError" class="rounded-2xl bg-error/10 px-4 py-3 text-sm text-error">
        <p>{{ lastError }}</p>
        <button class="mt-2 font-label-bold text-primary" @click="retry">{{ t('chat.retry') }}</button>
      </div>
    </main>

    <!-- 输入区 -->
    <div class="fixed bottom-0 left-0 right-0 z-30 border-t border-outline-variant/40 bg-background/90 px-4 pb-safe pt-3 backdrop-blur-xl">
      <div class="flex items-end gap-2">
        <button
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant transition-transform active:scale-90 disabled:opacity-50"
          :disabled="uploading || streaming"
          :aria-label="t('chat.upload')"
          @click="pickDocument"
        >
          <span class="material-symbols-outlined">{{ uploading ? 'progress_activity' : 'attach_file' }}</span>
        </button>
        <input
          ref="fileInput"
          type="file"
          class="hidden"
          accept=".txt,.md,.markdown,.csv,.json,.log,.yaml,.yml,.pdf,text/plain,application/pdf"
          @change="onFilePicked"
        />
        <textarea
          ref="input"
          v-model="draft"
          rows="1"
          :placeholder="t('chat.placeholder')"
          class="max-h-32 flex-1 resize-none rounded-2xl bg-surface-container-low px-4 py-3 text-sm text-on-surface outline-none placeholder:text-on-surface-variant/60"
          @keydown="onKeydown"
        />
        <button
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-transform active:scale-90"
          :class="canSend ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant/50'"
          :disabled="!canSend"
          :aria-label="t('chat.send')"
          @click="send()"
        >
          <span class="material-symbols-outlined">{{ streaming ? 'more_horiz' : 'send' }}</span>
        </button>
      </div>
      <p class="pb-2 pt-1.5 text-center text-[10px] text-on-surface-variant/60">
        {{ t('chat.disclaimer') }}
      </p>
    </div>

    <!-- 历史会话面板 -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0"
    >
      <div v-if="historyOpen" class="fixed inset-0 z-40">
        <div class="absolute inset-0 bg-black/30" @click="historyOpen = false" />
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="translate-y-full"
          leave-active-class="transition duration-150 ease-in"
          leave-to-class="translate-y-full"
          appear
        >
          <section
            class="absolute bottom-0 left-0 right-0 flex max-h-[70vh] flex-col rounded-t-3xl bg-surface pb-safe shadow-2xl"
            role="dialog"
            :aria-label="t('chat.history')"
          >
            <div class="flex items-center justify-between px-5 pb-2 pt-4">
              <p class="font-title-md text-on-surface">{{ t('chat.history') }}</p>
              <button
                class="flex h-8 w-8 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
                :aria-label="t('common.back')"
                @click="historyOpen = false"
              >
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div class="min-h-0 flex-1 overflow-y-auto px-3 pb-4 no-scrollbar">
              <p v-if="historyLoading" class="px-2 py-6 text-center text-sm text-on-surface-variant">
                {{ t('common.loading') }}
              </p>
              <p v-else-if="historyError" class="px-2 py-6 text-center text-sm text-error">
                {{ historyError }}
              </p>
              <p v-else-if="sessions.length === 0" class="px-2 py-6 text-center text-sm text-on-surface-variant">
                {{ t('chat.historyEmpty') }}
              </p>
              <button
                v-for="item in sessions"
                :key="item.id"
                class="mb-1 flex w-full items-start gap-3 rounded-2xl px-3 py-3 text-left active:bg-surface-container-low"
                :class="item.id === sessionId ? 'bg-primary/10' : ''"
                @click="openSession(item.id)"
              >
                <span class="material-symbols-outlined mt-0.5 text-xl text-primary/70">forum</span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm text-on-surface">{{ item.title || t('chat.newChat') }}</span>
                  <span class="mt-0.5 block text-[11px] text-on-surface-variant">
                    {{ formatWhen(item.create_time) }} · {{ t('chat.messageCount', { count: item.message_count }) }}
                  </span>
                </span>
              </button>
            </div>
          </section>
        </transition>
      </div>
    </transition>
  </div>
</template>
