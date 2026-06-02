import request from './request'

export const petApi = {
  listPage: (data: any) => request.post('/admin/pet/list/page/vo', data),
  delete: (id: number) => request.post('/admin/pet/delete', { id }),
}
