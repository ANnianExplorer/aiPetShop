import request from './request'

export const commentApi = {
  listPage: (data: any) => request.post('/admin/comment/list/page/vo', data),
  delete: (id: number) => request.post('/admin/comment/delete', { id }),
}
