import request from './request'

export const notificationApi = {
  listPage: (data: any) => request.post('/notification/list/page', data),
  unreadCount: () => request.get('/notification/unread/count'),
}
