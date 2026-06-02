export interface User {
  id: number
  phone?: string
  email?: string
  nickname?: string
  avatar?: string
  bio?: string
  location?: string
  role?: string
  status?: number
  createTime?: string
}

export interface Pet {
  id: number
  userId: number
  name: string
  avatar?: string
  type?: string
  breed?: string
  age?: string
  healthScore?: number
  todaySteps?: number
  user?: User
  createTime?: string
}

export interface Post {
  id: number
  authorId: number
  content: string
  imageList?: string[]
  tagList?: string[]
  category?: string
  likes: number
  comments: number
  user?: User
  createTime?: string
}

export interface Comment {
  id: number
  postId: number
  userId: number
  content: string
  likes: number
  user?: User
  createTime?: string
}

export interface Topic {
  id: number
  title: string
  description?: string
  image?: string
  category?: string
  postCount: number
  followerCount: number
  createTime?: string
}

export interface LogEntry {
  id: number
  userId: number
  petId: number
  type: string
  title: string
  content?: string
  imageList?: string[]
  tagList?: string[]
  likes: number
  user?: User
  createTime?: string
}

export interface HealthRecord {
  id: number
  petId: number
  date?: string
  heartRate?: number
  sleepHours?: number
  steps?: number
  calories?: number
  exercise?: number
  weight?: number
  waterIntake?: number
  mood?: string
  createTime?: string
}

export interface Notification {
  id: number
  userId: number
  type: string
  title: string
  content: string
  isRead: number
  createTime?: string
}

export interface PageResult<T> {
  records: T[]
  total: number
  current: number
  size: number
}

export interface DashboardStats {
  userTotal: number
  petTotal: number
  postTotal: number
  commentTotal: number
  topicTotal: number
  logTotal: number
  petTypeDistribution: Record<string, number>
  activeUserTrend: { date: string; count: number }[]
  hotPosts: any[]
  hotTopics: any[]
}
