import request from './request'

export const notificationApi = {
  listPage: (data: any) => request.post('/admin/notification/list/page/vo', data),
  delete: (id: number) => request.post('/admin/notification/delete', { id }),
}
