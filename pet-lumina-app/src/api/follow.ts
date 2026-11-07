import request from './request'
import type { PageResult, User } from '@/types'

export const followApi = {
  toggle: (userId: string | number): Promise<boolean> =>
    request.post<boolean>(`/follow/${String(userId)}`),

  listFollowers: (data?: { current?: number; pageSize?: number }): Promise<PageResult<User>> =>
    request.post<PageResult<User>>('/follow/list/followers', data || {}),

  listFollowing: (data?: { current?: number; pageSize?: number }): Promise<PageResult<User>> =>
    request.post<PageResult<User>>('/follow/list/following', data || {}),
}
