import request from './request'

export interface AdminUserSavePayload {
  id?: number | string
  phone?: string
  email?: string
  password?: string
  nickname?: string
  avatar?: string
  role?: 'user' | 'admin'
  status?: 0 | 1
}

export const userApi = {
  listPage: (data: any) => request.post('/admin/user/list/page/vo', data),
  getDetail: (id: number | string) => request.get('/admin/user/get/vo', { params: { id: String(id) } }),
  updateStatus: (data: { id: number; status: number }) =>
    request.post('/admin/user/update/status', data),
  add: (data: AdminUserSavePayload) => request.post('/admin/user/add', data),
  update: (data: AdminUserSavePayload) => request.post('/admin/user/update', data),
}
