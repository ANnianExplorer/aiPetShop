import request from './request'

export const petApi = {
  listPage: (data: any) => request.post('/admin/pet/list/page/vo', data),
  getDetail: (id: string | number) => request.get('/pet/get/vo', { params: { id: String(id) } }),
  add: (data: any) => request.post('/pet/add', data),
  edit: (data: any) => request.post('/pet/edit', data),
  delete: (id: number) => request.post('/admin/pet/delete', { id }),
}
