import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import type { User } from '@/types'

export const useAdminStore = defineStore('admin', () => {
  const currentUser = ref<User | null>(null)
  const isLoggedIn = ref(false)

  async function login(phone: string, password: string) {
    const res = await authApi.login({ phone, password }) as any
    if (res?.token) {
      localStorage.setItem('satoken', res.token)
      isLoggedIn.value = true
      currentUser.value = {
        id: res.id,
        nickname: res.nickname,
        avatar: res.avatar,
        phone: res.phone,
      }
    }
    return res
  }

  async function fetchCurrentUser() {
    try {
      const res = await authApi.getCurrent() as any
      currentUser.value = res
      isLoggedIn.value = true
    } catch {
      currentUser.value = null
      isLoggedIn.value = false
    }
  }

  function logout() {
    localStorage.removeItem('satoken')
    currentUser.value = null
    isLoggedIn.value = false
  }

  return { currentUser, isLoggedIn, login, fetchCurrentUser, logout }
})
