import request from './request'

export const healthApi = {
  listRecords: (data: any) => request.post('/admin/health/record/list/page', data),
  getRecordDetail: (id: number | string) => request.get('/admin/health/record/detail', { params: { id: String(id) } }),
}
