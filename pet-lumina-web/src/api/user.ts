import request from './request'

export const userApi = {
  listPage: (data: any) => request.post('/admin/user/list/page/vo', data),
  getDetail: (id: number | string) => request.get('/admin/user/get/vo', { params: { id: String(id) } }),
  updateStatus: (data: { id: number; status: number }) =>
    request.post('/admin/user/update/status', data),
}
