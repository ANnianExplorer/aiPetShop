import request from './request'

export const notificationApi = {
  listPage: (data: { current?: number; pageSize?: number; type?: string; isRead?: number }) =>
    request.post('/notification/list/page', data),

  getDetail: (id: number | string) =>
    request.get('/notification/detail', { params: { id: String(id) } }),

  unreadCount: () =>
    request.get('/notification/unread/count'),

  markAsRead: (id: number | string) =>
    request.post(`/notification/read/${String(id)}`),

  markAllAsRead: () =>
    request.post('/notification/read/all'),
}
