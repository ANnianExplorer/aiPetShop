import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, Pet, Reminder, PetHealthData, HealthPlan } from '@/types'
import { authApi } from '@/api/auth'
import { petApi } from '@/api/pet'
import { reminderApi } from '@/api/reminder'
import { healthApi } from '@/api/health'
import { notificationApi } from '@/api/notification'

export const useUserStore = defineStore('user', () => {
  const currentUser = ref<User | null>(null)
  const currentPet = ref<Pet | null>(null)
  const pets = ref<Pet[]>([])
  const tasks = ref<Reminder[]>([])
  const healthPlans = ref<HealthPlan[]>([])
  const petHealthData = ref<Record<string, PetHealthData>>({})
  const loading = ref(false)
  const unreadNotifications = ref(0)

  const getPetById = computed(() => (id: string | number) => {
    // 后端 id 是字符串化的雪花号，这里统一按字符串比较
    return pets.value.find(pet => pet.id === String(id))
  })

  const getTasksByPetId = computed(() => (petId: string) => {
    return tasks.value.filter(task => task.petId === petId)
  })

  const getHealthDataByPetId = computed(() => (petId: string) => {
    return petHealthData.value[petId] || null
  })

  const getHealthPlansByPetId = computed(() => (petId: string) => {
    return healthPlans.value.filter(plan => plan.petId === petId)
  })

  // 获取当前登录用户
  const fetchCurrentUser = async () => {
    try {
      const user = await authApi.getCurrentUser()
      currentUser.value = user
      return user
    } catch (e) {
      currentUser.value = null
      return null
    }
  }

  // 获取宠物列表
  const fetchPets = async () => {
    try {
      const list = await petApi.list()
      pets.value = list || []
      if (pets.value.length > 0 && !currentPet.value) {
        currentPet.value = pets.value[0]
      }
    } catch (e) {
      pets.value = []
    }
  }

  // 获取当前宠物的健康数据
  const fetchHealthData = async (petId: string) => {
    try {
      const data = await healthApi.dashboard(petId)
      petHealthData.value[petId] = data
    } catch (e) {
      // ignore
    }
  }

  // 获取当前宠物的提醒列表
  const fetchTasks = async (petId?: string) => {
    try {
      const params: { pageSize: number; petId?: string } = { pageSize: 50 }
      if (petId) params.petId = petId
      const res = await reminderApi.listPage(params)
      tasks.value = res?.records || []
    } catch (e) {
      tasks.value = []
    }
  }

  // 获取当前宠物的健康计划
  const fetchHealthPlans = async (petId: string) => {
    try {
      const res = await healthApi.planListPage({ petId, pageSize: 50 })
      healthPlans.value = res?.records || []
    } catch (e) {
      healthPlans.value = []
    }
  }

  // 初始化加载
  const fetchUnreadNotifications = async () => {
    try {
      unreadNotifications.value = (await notificationApi.unreadCount()) || 0
    } catch {}
  }

  const init = async () => {
    loading.value = true
    try {
      await fetchCurrentUser()
      await fetchPets()
      fetchUnreadNotifications()
      if (currentPet.value) {
        await Promise.all([
          fetchHealthData(currentPet.value.id),
          fetchTasks(currentPet.value.id),
          fetchHealthPlans(currentPet.value.id),
        ])
      }
    } finally {
      loading.value = false
    }
  }

  const updateAvatar = async (avatar: string) => {
    if (currentUser.value) {
      currentUser.value.avatar = avatar
    }
  }

  const updatePet = async (petId: string, updates: Partial<Pet>) => {
    await petApi.edit({ id: petId, ...updates })
    await fetchPets()
    if (currentPet.value?.id === petId) {
      currentPet.value = pets.value.find(p => p.id === petId) || null
    }
  }

  const addPet = async (pet: { name: string; type: string; breed?: string; age?: string; notes?: string; avatar?: string }) => {
    await petApi.add(pet)
    await fetchPets()
  }

  const switchCurrentPet = (petId: string) => {
    const pet = pets.value.find(p => p.id === petId)
    if (pet) {
      currentPet.value = pet
      fetchHealthData(petId)
      fetchTasks(petId)
      fetchHealthPlans(petId)
    }
  }

  const updateTaskCompletion = async (taskId: string) => {
    await reminderApi.toggleComplete(taskId)
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.isCompleted = task.isCompleted === 1 ? 0 : 1
    }
  }

  // 登录
  const login = async (phone: string, password: string) => {
    const res = await authApi.login({ phone, password })
    localStorage.setItem('satoken', res.token || '')
    await init()
    return res
  }

  // 注册
  const register = async (phone: string, code: string, password: string) => {
    const res = await authApi.register({ phone, code, password })
    localStorage.setItem('satoken', res.token || '')
    await init()
    return res
  }

  // 登出
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('satoken')
    currentUser.value = null
    currentPet.value = null
    pets.value = []
    tasks.value = []
    petHealthData.value = {}
  }

  return {
    currentUser,
    currentPet,
    pets,
    petHealthData,
    tasks,
    healthPlans,
    loading,
    unreadNotifications,
    getPetById,
    getTasksByPetId,
    getHealthDataByPetId,
    getHealthPlansByPetId,
    fetchCurrentUser,
    fetchPets,
    fetchHealthData,
    fetchTasks,
    fetchHealthPlans,
    fetchUnreadNotifications,
    init,
    updateAvatar,
    updatePet,
    addPet,
    switchCurrentPet,
    updateTaskCompletion,
    login,
    register,
    logout,
  }
})
