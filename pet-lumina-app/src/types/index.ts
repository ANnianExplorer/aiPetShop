// 全局 TypeScript 类型定义

export interface User {
  id: string
  name: string
  avatar: string
  location?: string
}

export interface Pet {
  id: string
  name: string
  avatar: string
  type: 'dog' | 'cat' | 'other'
  breed: string
  age: string
  healthScore: number
  todaySteps: number
  feedingCount: number
  feedingTotal: number
}

export interface Reminder {
  id: string
  petId: string
  title: string
  time: string
  location: string
  type: 'medical' | 'daily' | 'activity'
  isCompleted: boolean
  standard?: 'steps' | 'calories' | 'exercise' | 'sleep' | 'heartRate'
  standardValue?: string
}

export interface Post {
  id: string
  author: User
  content: string
  images: string[]
  tags: string[]
  createdAt: string
  likes: number
  comments: number
  category?: string
  isLiked?: boolean
  isBookmarked?: boolean
}

export interface Topic {
  id: string
  title: string
  image: string
  category: string
}

export interface LogEntry {
  id: string
  petId: string
  type: 'feeding' | 'walking' | 'grooming' | 'medical' | 'other'
  title: string
  description: string
  images: string[]
  createdAt: string
  tags: string[]
}
