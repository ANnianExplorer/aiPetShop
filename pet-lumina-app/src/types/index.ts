// 全局 TypeScript 类型定义
// 注意：后端所有 Long 型 id 都经 JsonConfig 序列化为字符串（19 位雪花号超过
// JS 安全整数范围），因此这里所有 id / *Id 字段一律使用 string。

/** 分页结果：MyBatis Plus IPage 序列化后的常用字段子集 */
export interface PageResult<T> {
  records: T[]
  total: number
  current?: number
  pageSize?: number
}

export interface User {
  id: string
  nickname: string
  avatar: string
  bio?: string
  location?: string
  phone?: string
  email?: string
  role?: string
  status?: number
  token?: string
}

/** 登录 / 当前用户接口返回（后端 LoginUserVO） */
export interface LoginUser extends User {
  token?: string
}

export interface Pet {
  id: string
  userId: string
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
  id: string
  userId: string
  petId: string
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
  id: string
  authorId: string
  content: string
  imageList: string[]
  tagList: string[]
  category?: string
  topicId?: string
  likes: number
  comments: number
  isLiked?: number
  isFavorited?: number
  user?: User
  createTime: string
}

export interface Topic {
  id: string
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
  id: string
  userId: string
  petId: string
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
  id: string
  postId: string
  userId: string
  content: string
  parentId?: string
  likes: number
  /** 后端 CommentVO 暂未返回该字段，前端按未点赞（0）处理 */
  isLiked?: number
  user?: User
  children?: Comment[]
  createTime: string
}

export interface Notification {
  id: string
  userId: string
  type: 'reminder' | 'social' | 'health' | 'system'
  title: string
  content: string
  isRead: number
  status?: number
  relatedId?: string
  createTime: string
}

/**
 * 健康数据：既是 dashboard 聚合结果，也是单条健康记录
 * （后端 HealthDashboardVO / HealthRecordVO）
 */
export interface PetHealthData {
  id?: string
  petId?: string
  date?: string
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
  createTime?: string
}

export interface HealthPlan {
  id: string
  petId: string
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

// 请求类型（id 参数统一兼容 string | number）
export interface PetAddRequest {
  name: string
  type: string
  breed?: string
  age?: string
  notes?: string
  avatar?: string
}

export interface PetEditRequest {
  id: string | number
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
  topicId?: string | number
  authorId?: string | number
}
