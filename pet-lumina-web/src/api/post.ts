import request from './request'

export const postApi = {
  listPage: (data: any) => request.post('/admin/post/list/page/vo', data),
  delete: (id: number) => request.post('/admin/post/delete', { id }),
}
