import request from './request'

export const topicApi = {
  listPage: (data: any) => request.post('/admin/topic/list/page/vo', data),
  add: (data: any) => request.post('/admin/topic/add', data),
  edit: (data: any) => request.post('/admin/topic/edit', data),
  delete: (id: number) => request.post('/admin/topic/delete', { id }),
}
