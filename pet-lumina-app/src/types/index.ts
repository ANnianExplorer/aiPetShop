// 全局 TypeScript 类型定义

export interface User {
  id: number
  nickname: string
  avatar: string
  bio?: string
  location?: string
  phone?: string
  email?: string
  token?: string
}

export interface Pet {
  id: number
  userId: number
  name: string
  avatar: string
  type: 'dog' | 'cat' | 'other'
  breed: string
  age: string
  healthScore: number
  todaySteps: number
  feedingCount: number
  feedingTotal: number
  notes?: string
  createTime?: string
}

export interface Reminder {
  id: number
  userId: number
  petId: number
  title: string
  type: 'medical' | 'daily' | 'activity'
  remindTime: string
  location?: string
  repeatType?: 'none' | 'daily' | 'weekly' | 'monthly'
  notes?: string
  isCompleted: number
  createTime?: string
}

export interface Post {
  id: number
  authorId: number
  content: string
  imageList: string[]
  tagList: string[]
  category?: string
  likes: number
  comments: number
  isLiked?: number
  isFavorited?: number
  user?: User
  createTime: string
}

export interface Topic {
  id: number
  title: string
  description?: string
  image?: string
  category?: string
  postCount: number
  followerCount: number
  isFollowed?: number
  createTime?: string
}

export interface LogEntry {
  id: number
  userId: number
  petId: number
  type: 'feeding' | 'walking' | 'grooming' | 'medical' | 'other'
  title: string
  content: string
  imageList: string[]
  tagList: string[]
  likes: number
  user?: User
  createTime: string
}

export interface Comment {
  id: number
  postId: number
  userId: number
  content: string
  parentId?: number
  likes: number
  user?: User
  children?: Comment[]
  createTime: string
}

export interface Notification {
  id: number
  userId: number
  type: 'reminder' | 'social' | 'health' | 'system'
  title: string
  content: string
  isRead: number
  relatedId?: number
  createTime: string
}

export interface PetHealthData {
  weight?: number
  weightChange?: string
  heartRate?: number
  sleepHours?: number
  steps?: number
  calories?: number
  exercise?: number
  waterIntake?: number
  mood?: string
  yesterdayData?: PetHealthData
  weeklyData?: PetHealthData[]
}

export interface HealthPlan {
  id: number
  petId: number
  type: 'feeding' | 'exercise' | 'medical' | 'grooming' | 'training'
  title: string
  time?: string
  frequency?: string
  standard?: string
  standardValue?: number
  notes?: string
  isActive?: number
  createTime?: string
}

// 请求类型
export interface PetAddRequest {
  name: string
  type: string
  breed?: string
  age?: string
  notes?: string
  avatar?: string
}

export interface PetEditRequest {
  id: number
  name?: string
  breed?: string
  type?: string
  age?: string
  notes?: string
  avatar?: string
}

export interface PetQueryRequest {
  current?: number
  pageSize?: number
  name?: string
  type?: string
}

export interface PostQueryRequest {
  current?: number
  pageSize?: number
  category?: string
  searchText?: string
  topicId?: number
  authorId?: number
}
