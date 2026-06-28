import request from './request'

export const topicApi = {
  add: (data: { title: string; description?: string; image?: string; category?: string }) =>
    request.post('/topic/add', data),

  edit: (data: { id: number; title?: string; description?: string; image?: string; category?: string }) =>
    request.post('/topic/edit', data),

  delete: (id: number) =>
    request.post('/topic/delete', { id }),

  getById: (id: number | string) =>
    request.get('/topic/get/vo', { params: { id: String(id) } }),

  listPage: (data: { current?: number; pageSize?: number; category?: string; searchText?: string }) =>
    request.post('/topic/list/page/vo', data),

  toggleFollow: (id: number) =>
    request.post(`/topic/follow/${id}`),

  listTopicPosts: (data: { topicId: number; current?: number; pageSize?: number }) =>
    request.post('/topic/list/page/vo/posts', data),
}
