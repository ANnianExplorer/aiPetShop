import request from './request'

export const logApi = {
  add: (data: { petId: number; type: string; title: string; content: string; images?: string; tags?: string }) =>
    request.post('/log/add', data),

  edit: (data: { id: number; title?: string; content?: string; images?: string; tags?: string }) =>
    request.post('/log/edit', data),

  delete: (id: number) =>
    request.post('/log/delete', { id }),

  getById: (id: number) =>
    request.get('/log/get/vo', { params: { id } }),

  listPage: (data: { current?: number; pageSize?: number; type?: string; petId?: number }) =>
    request.post('/log/list/page/vo', data),
}
