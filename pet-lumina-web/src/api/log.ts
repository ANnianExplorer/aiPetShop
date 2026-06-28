import request from './request'

export const logApi = {
  listPage: (data: any) => request.post('/admin/log/list/page/vo', data),
  getById: (id: number | string) => request.get('/log/get/vo', { params: { id: String(id) } }),
  delete: (id: number) => request.post('/admin/log/delete', { id }),
}
