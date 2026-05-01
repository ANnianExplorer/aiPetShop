import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, Pet, Reminder } from '@/types'

export interface PetHealthData {
  petId: string
  weight: number
  weightChange: string
  heartRate: number
  sleepHours: number
  steps: number
  calories: number
  exercise: number
  metRate: number
  yesterdayData: {
    heartRate: number
    sleepHours: number
    steps: number
    calories: number
    exercise: number
    metRate: number
  }
  weeklyData: {
    heartRate: number
    sleepHours: number
  }
}

export const useUserStore = defineStore('user', () => {
  const currentUser = ref<User | null>({
    id: 'u1',
    name: '柚子妈妈',
    avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD6LoELJc0xR0KOhiDVYA51ZM_SAGysj8LyNbRsT3xixwHAy3lGwWcDJuCq08SF8omXqVVIzZsKl1i6wxxuSIS50V_x8X4hpt3NIUwba9rkMf7IoiYTpZ4QFmtkNW0jtUEj6H1eDfS9XxwwY4bhg-B0U1qVNaYRhf-3v723-4nYHk9yQD8no-RC29SWNTKeBFuzy_vXZH0mXx3IBMkG61n0rcuYT3AtisWc3tz2UhIU04ydqzEUqHFrD1K_ailZMIL5o7kJzcIyYjUh',
    location: '北京'
  })

  const currentPet = ref<Pet | null>({
    id: 'p1',
    name: '柚子',
    avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBXMA-i_H_Dsn3BuMszAgnCl-8BpmS71NPY1j3T-77zZDfzWPhBcdDRxY3Xmq8aePeM7pTAG0kqqBVWExc7IekEkhQqQ6HaRJ50AP24EmSEQyxPSiWw6BJvowqGHeecgJ7ChfVGrXRL3jRUcptDSudBLK-fKWguQcsOd1au27mJoNZNJVzBDZbAhkTDDVFfHdeaTcxg0uRwwebxTjI_gOOq3vBXbhfy4fWHrqJKuOlB0iY3j6_LPkkpk99z36r-ghqqfPKjsI_qK1Ft',
    type: 'dog',
    breed: '金毛寻回犬',
    age: '2岁',
    healthScore: 98,
    todaySteps: 7420,
    feedingCount: 2,
    feedingTotal: 3
  })

  const pets = ref<Pet[]>([
    currentPet.value!,
    {
      id: 'p2',
      name: '煤球',
      avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD00PWY2nM3BHxtT5pNQtzTMQpJ4-ji8Tz4tb_Tb421DMXlYpF7C3-Y9CXxh63oUyJF9I9OOiF9YTgR-PxLaCpQwrievY8n-OLamjLhtf7gdm_dWO968KjhWFs2VC-3FvZaZb6uwhuXadzjZcj0r0D4SMg3s4fPVwl12QdRsVz9FmDxevpdbuwX6aZq6J44LMBXKrLIVkPdNTRXJ1xCObPJL-nvYQf1b9czt4GVn0hTmVohZlzAKC022e1sVmuWvJzmc9EA0kYRXQBs',
      type: 'cat',
      breed: '英国短毛猫',
      age: '3岁',
      healthScore: 95,
      todaySteps: 2000,
      feedingCount: 2,
      feedingTotal: 2
    },
    {
      id: 'p3',
      name: '芝士',
      avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCLomEeR9UcPB06welofXACWruHN35RRETEkmNDsd-oCL8f1dwFZf0veXGSGHveOr6fMmlaTrDS6Hpyk_s6DmhbaHP19UxPu5MVgHT8KP5P_BQBOOaQfRtw7QEw85nsC3Q4KEvU9vCQ59s0tc1w3jcjdE3IHMMnWWAZrrjEeV5W9z0lOVAH5mpKnu4awC6pOb8X64oq1cSLUEWwVqvvPe7kxT7K8YDqm-AZe430Vug8IEA0QTWytPfs4KsoeRQgbMrp-wrrHfCITJjd',
      type: 'cat',
      breed: '中华田园猫',
      age: '1岁',
      healthScore: 99,
      todaySteps: 3500,
      feedingCount: 1,
      feedingTotal: 3
    }
  ])

  const petHealthData = ref<Record<string, PetHealthData>>({
    p1: {
      petId: 'p1',
      weight: 12.5,
      weightChange: '+2.4%',
      heartRate: 78,
      sleepHours: 9.2,
      steps: 7420,
      calories: 480,
      exercise: 50,
      metRate: 85,
      yesterdayData: {
        heartRate: 76,
        sleepHours: 9.5,
        steps: 7200,
        calories: 450,
        exercise: 45,
        metRate: 80
      },
      weeklyData: {
        heartRate: 78,
        sleepHours: 9.2
      }
    },
    p2: {
      petId: 'p2',
      weight: 4.8,
      weightChange: '+0.3%',
      heartRate: 65,
      sleepHours: 12.5,
      steps: 2000,
      calories: 280,
      exercise: 20,
      metRate: 90,
      yesterdayData: {
        heartRate: 68,
        sleepHours: 13.0,
        steps: 1800,
        calories: 260,
        exercise: 18,
        metRate: 88
      },
      weeklyData: {
        heartRate: 65,
        sleepHours: 12.5
      }
    },
    p3: {
      petId: 'p3',
      weight: 3.2,
      weightChange: '+1.2%',
      heartRate: 72,
      sleepHours: 11.0,
      steps: 3500,
      calories: 320,
      exercise: 30,
      metRate: 92,
      yesterdayData: {
        heartRate: 70,
        sleepHours: 10.5,
        steps: 3200,
        calories: 300,
        exercise: 28,
        metRate: 90
      },
      weeklyData: {
        heartRate: 72,
        sleepHours: 11.0
      }
    }
  })

  const tasks = ref<Reminder[]>([
    {
      id: 't1',
      petId: 'p1',
      title: '晨间喂食',
      time: '08:00 AM',
      location: '200g 幼犬粮',
      type: 'daily',
      isCompleted: false,
      standard: 'calories',
      standardValue: '320kcal'
    },
    {
      id: 't2',
      petId: 'p1',
      title: '户外散步',
      time: '09:30 AM',
      location: '30分钟',
      type: 'activity',
      isCompleted: true,
      standard: 'steps',
      standardValue: '5000步'
    },
    {
      id: 't3',
      petId: 'p1',
      title: '补充维生素',
      time: '12:00 PM',
      location: '1片',
      type: 'medical',
      isCompleted: false
    },
    {
      id: 't4',
      petId: 'p1',
      title: '下午训练',
      time: '03:00 PM',
      location: '飞盘训练',
      type: 'activity',
      isCompleted: false,
      standard: 'exercise',
      standardValue: '30分钟'
    },
    {
      id: 't5',
      petId: 'p2',
      title: '晨间喂食',
      time: '08:30 AM',
      location: '150g 成猫粮',
      type: 'daily',
      isCompleted: true,
      standard: 'calories',
      standardValue: '280kcal'
    },
    {
      id: 't6',
      petId: 'p2',
      title: '梳理毛发',
      time: '10:00 AM',
      location: '15分钟',
      type: 'daily',
      isCompleted: false
    },
    {
      id: 't7',
      petId: 'p2',
      title: '互动玩耍',
      time: '04:00 PM',
      location: '逗猫棒',
      type: 'activity',
      isCompleted: false,
      standard: 'exercise',
      standardValue: '20分钟'
    },
    {
      id: 't8',
      petId: 'p3',
      title: '晨间喂食',
      time: '08:00 AM',
      location: '100g 幼猫粮',
      type: 'daily',
      isCompleted: true,
      standard: 'calories',
      standardValue: '200kcal'
    },
    {
      id: 't9',
      petId: 'p3',
      title: '室内活动',
      time: '11:00 AM',
      location: '自由活动',
      type: 'activity',
      isCompleted: false,
      standard: 'steps',
      standardValue: '3000步'
    },
    {
      id: 't10',
      petId: 'p3',
      title: '补充营养膏',
      time: '02:00 PM',
      location: '5cm',
      type: 'medical',
      isCompleted: false
    }
  ])

  const getPetById = computed(() => (id: string) => {
    return pets.value.find(pet => pet.id === id)
  })

  const getTasksByPetId = computed(() => (petId: string) => {
    return tasks.value.filter(task => task.petId === petId)
  })

  const getHealthDataByPetId = computed(() => (petId: string) => {
    return petHealthData.value[petId] || null
  })

  const updateAvatar = (avatar: string) => {
    if (currentUser.value) {
      currentUser.value.avatar = avatar
    }
  }

  const updatePet = (petId: string, updates: Partial<Pet>) => {
    const index = pets.value.findIndex(p => p.id === petId)
    if (index !== -1) {
      pets.value[index] = { ...pets.value[index], ...updates }
    }
  }

  const addPet = (pet: Pet) => {
    pets.value.push(pet)
  }

  const switchCurrentPet = (petId: string) => {
    const pet = pets.value.find(p => p.id === petId)
    if (pet) {
      currentPet.value = pet
    }
  }

  const updateTaskCompletion = (taskId: string, isCompleted: boolean) => {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.isCompleted = isCompleted
    }
  }

  return {
    currentUser,
    currentPet,
    pets,
    petHealthData,
    tasks,
    getPetById,
    getTasksByPetId,
    getHealthDataByPetId,
    updateAvatar,
    updatePet,
    addPet,
    switchCurrentPet,
    updateTaskCompletion
  }
})
