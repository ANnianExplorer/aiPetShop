import request from './request'

export const postApi = {
  listPage: (data: any) => request.post('/admin/post/list/page/vo', data),
  getDetail: (id: string | number) => request.get('/post/get/vo', { params: { id } }),
  delete: (id: number) => request.post('/admin/post/delete', { id }),
}
