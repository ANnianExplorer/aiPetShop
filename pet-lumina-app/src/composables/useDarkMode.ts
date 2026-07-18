import { ref, watch } from 'vue'

const STORAGE_KEY = 'petlumina-dark-mode'

const isDark = ref(false)

// 初始化：从 localStorage 读取
function initDarkMode() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved !== null) {
    isDark.value = saved === 'true'
  } else {
    // 跟随系统偏好
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  applyDarkMode()
}

// 应用到 DOM
function applyDarkMode() {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 切换深色模式
function toggleDarkMode() {
  isDark.value = !isDark.value
}

// 监听变化，持久化 + 应用
watch(isDark, (val) => {
  localStorage.setItem(STORAGE_KEY, String(val))
  applyDarkMode()
})

export function useDarkMode() {
  return {
    isDark,
    toggleDarkMode,
    initDarkMode,
  }
}
