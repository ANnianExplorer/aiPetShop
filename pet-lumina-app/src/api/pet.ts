import request from './request'

export const petApi = {
  add: (data: { name: string; type: string; breed?: string; age?: string; notes?: string; avatar?: string }) =>
    request.post('/pet/add', data),

  edit: (data: { id: number; name?: string; breed?: string; age?: string; notes?: string; avatar?: string }) =>
    request.post('/pet/edit', data),

  delete: (id: number) =>
    request.post('/pet/delete', { id }),

  getById: (id: number) =>
    request.get('/pet/get/vo', { params: { id } }),

  list: () =>
    request.get('/pet/list'),

  listPage: (data: { current?: number; pageSize?: number; name?: string; type?: string }) =>
    request.post('/pet/list/page/vo', data),
}
