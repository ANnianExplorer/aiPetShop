import request from './request'

export const notificationApi = {
  listPage: (data: any) => request.post('/admin/notification/list/page/vo', data),
  create: (data: { title: string; content: string; type: string }) => request.post('/admin/notification/add', data),
  update: (data: { id: number; title?: string; content?: string; type?: string }) => request.post('/admin/notification/update', data),
  toggleStatus: (id: number, status: number) => request.post('/admin/notification/toggle-status', { id, status }),
  delete: (id: number) => request.post('/admin/notification/delete', { id }),
}
