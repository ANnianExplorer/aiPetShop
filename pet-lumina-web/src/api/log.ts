import request from './request'

export const logApi = {
  listPage: (data: any) => request.post('/admin/log/list/page/vo', data),
  delete: (id: number) => request.post('/admin/log/delete', { id }),
}
