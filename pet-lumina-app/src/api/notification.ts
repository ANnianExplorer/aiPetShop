import request from './request'
import type { Notification, PageResult } from '@/types'

export const notificationApi = {
  listPage: (data: { current?: number; pageSize?: number; type?: string; isRead?: number }): Promise<PageResult<Notification>> =>
    request.post<PageResult<Notification>>('/notification/list/page', data),

  getDetail: (id: string | number): Promise<Notification> =>
    request.get<Notification>('/notification/detail', { params: { id: String(id) } }),

  unreadCount: async (): Promise<number> => {
    // 后端该接口返回 Long，JsonConfig 会序列化成字符串，这里统一收敛为 number
    const count = await request.get<string | number>('/notification/unread/count')
    return Number(count) || 0
  },

  markAsRead: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/notification/read/${String(id)}`),

  markAllAsRead: (): Promise<boolean> =>
    request.post<boolean>('/notification/read/all'),
}
