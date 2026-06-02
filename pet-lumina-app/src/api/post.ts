import request from './request'

export const postApi = {
  add: (data: { content: string; images?: string; tags?: string; category?: string }) =>
    request.post('/post/add', data),

  edit: (data: { id: number; content?: string; images?: string; tags?: string; category?: string }) =>
    request.post('/post/edit', data),

  delete: (id: number) =>
    request.post('/post/delete', { id }),

  getById: (id: number) =>
    request.get('/post/get/vo', { params: { id } }),

  listPage: (data: { current?: number; pageSize?: number; category?: string; searchText?: string; topicId?: number; authorId?: number }) =>
    request.post('/post/list/page/vo', data),

  toggleLike: (id: number) =>
    request.post(`/post/like/${id}`),

  toggleFavorite: (id: number) =>
    request.post(`/post/favorite/${id}`),
}
